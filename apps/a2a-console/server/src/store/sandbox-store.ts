import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

import { resolveSafePath } from '../lib/path-guard.js';
import { lockManager } from './lock-manager.js';
import type { Project } from './project-registry.js';
import { runPool } from './run-pool.js';

const MAX_SANDBOX_BYTES = 100 * 1024 * 1024;
const MAX_PATCH_BYTES = 5 * 1024 * 1024;
const MAX_APPLY_FILES = 50;

interface SnapshotEntry {
  path: string;
  size: number;
  mtime_ms: number;
  hash: string;
}

interface SandboxSnapshot {
  run_id: string;
  project_id: string;
  project_root: string;
  sandbox_path: string;
  source_files: SnapshotEntry[];
  created_at: string;
}

interface BackupEntry {
  path: string;
  backup_path: string;
  hash: string;
  size: number;
}

interface AppliedManifest {
  run_id: string;
  applied_files: string[];
  backups: BackupEntry[];
  applied_at: string;
}

export interface SandboxInitResult {
  run_id: string;
  project_id: string;
  sandbox_path: string;
  source_files: string[];
  total_size_bytes: number;
  created_at: string;
}

export interface SandboxDiffResult {
  run_id: string;
  changed_files: string[];
  patch: string;
  patch_size_bytes: number;
}

export interface SandboxApplyResult {
  run_id: string;
  applied_files: string[];
  backup_manifest_path: string;
  applied_at: string;
}

export interface SandboxRollbackResult {
  run_id: string;
  restored_files: string[];
  rolled_back_at: string;
}

export function initSandbox(
  runId: string,
  project: Project,
  sourceFiles: string[],
): SandboxInitResult {
  const normalized = normalizeSourceFiles(sourceFiles);
  const allowedFiles = normalized.map((file) => assertAllowedFile(project, file));
  const totalSize = allowedFiles.reduce((sum, file) => sum + file.size, 0);
  if (totalSize > MAX_SANDBOX_BYTES) {
    throw codedError('SANDBOX_TOO_LARGE', 'Sandbox source files exceed 100 MB');
  }

  const now = new Date().toISOString();
  const sandboxPath = sandboxRoot(project.project_root, runId);
  const workspacePath = path.join(sandboxPath, 'workspace-copy');
  fs.mkdirSync(workspacePath, { recursive: true });
  fs.mkdirSync(path.join(sandboxPath, 'patches'), { recursive: true });
  fs.mkdirSync(path.join(sandboxPath, 'logs'), { recursive: true });
  fs.mkdirSync(path.join(sandboxPath, 'test-results'), { recursive: true });
  fs.mkdirSync(path.join(sandboxPath, 'backups'), { recursive: true });

  const snapshot: SandboxSnapshot = {
    run_id: runId,
    project_id: project.project_id,
    project_root: project.project_root,
    sandbox_path: sandboxPath,
    source_files: [],
    created_at: now,
  };

  for (const file of allowedFiles) {
    const destination = path.join(workspacePath, file.relativePath);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(file.absPath, destination);
    snapshot.source_files.push({
      path: file.relativePath,
      size: file.size,
      mtime_ms: file.mtimeMs,
      hash: hashFile(file.absPath),
    });
  }

  writeJson(snapshotPath(sandboxPath), snapshot);
  runPool.update(runId, { sandbox_path: sandboxPath });

  return {
    run_id: runId,
    project_id: project.project_id,
    sandbox_path: sandboxPath,
    source_files: normalized,
    total_size_bytes: totalSize,
    created_at: now,
  };
}

export function diffSandbox(runId: string, projectRoot: string): SandboxDiffResult {
  const snapshot = loadSnapshot(projectRoot, runId);
  const changedFiles: string[] = [];
  const patchParts: string[] = [];
  for (const entry of snapshot.source_files) {
    const projectFile = resolveSafePath(snapshot.project_root, entry.path);
    const sandboxFile = path.join(snapshot.sandbox_path, 'workspace-copy', entry.path);
    const oldText = readTextIfExists(projectFile);
    const newText = readTextIfExists(sandboxFile);
    if (oldText === newText) continue;
    changedFiles.push(entry.path);
    patchParts.push(generateUnifiedDiff(oldText, newText, entry.path));
  }
  const patch = patchParts.filter(Boolean).join('\n');
  const patchSize = Buffer.byteLength(patch, 'utf8');
  if (patchSize > MAX_PATCH_BYTES) {
    throw codedError('SANDBOX_TOO_LARGE', 'Sandbox patch exceeds 5 MB');
  }
  if (patch.length > 0) writePatch(snapshot.sandbox_path, patch);
  return {
    run_id: runId,
    changed_files: changedFiles,
    patch,
    patch_size_bytes: patchSize,
  };
}

export function applySandbox(runId: string, projectRoot: string): SandboxApplyResult {
  const snapshot = loadSnapshot(projectRoot, runId);
  const diff = diffSandbox(runId, projectRoot);
  if (diff.changed_files.length >= MAX_APPLY_FILES) {
    throw codedError('SANDBOX_APPLY_TOO_MANY_FILES', 'Sandbox apply touches 50 or more files');
  }

  const lockResult = lockManager.acquire(runId, diff.changed_files);
  if (lockResult === 'waiting') {
    throw codedError('LOCK_WAITING', 'Sandbox apply is waiting for file locks');
  }

  try {
    assertSnapshotClean(snapshot, diff.changed_files);
    const appliedAt = new Date().toISOString();
    const backups = createBackups(snapshot, diff.changed_files, appliedAt);
    for (const relativePath of diff.changed_files) {
      const source = path.join(snapshot.sandbox_path, 'workspace-copy', relativePath);
      const target = resolveSafePath(snapshot.project_root, relativePath);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(source, target);
    }
    const manifest: AppliedManifest = {
      run_id: runId,
      applied_files: diff.changed_files,
      backups,
      applied_at: appliedAt,
    };
    const manifestPath = path.join(snapshot.sandbox_path, 'applied.json');
    writeJson(manifestPath, manifest);
    return {
      run_id: runId,
      applied_files: diff.changed_files,
      backup_manifest_path: manifestPath,
      applied_at: appliedAt,
    };
  } finally {
    lockManager.release(runId);
  }
}

export function rollbackSandbox(runId: string, projectRoot: string): SandboxRollbackResult {
  const snapshot = loadSnapshot(projectRoot, runId);
  const manifestPath = path.join(snapshot.sandbox_path, 'applied.json');
  if (!fs.existsSync(manifestPath)) {
    throw codedError('ROLLBACK_BACKUP_NOT_FOUND', 'applied.json not found');
  }
  const manifest = readJson<AppliedManifest>(manifestPath);
  const lockResult = lockManager.acquire(runId, manifest.applied_files);
  if (lockResult === 'waiting') {
    throw codedError('LOCK_WAITING', 'Sandbox rollback is waiting for file locks');
  }

  try {
    const restored: string[] = [];
    for (const backup of manifest.backups) {
      if (!fs.existsSync(backup.backup_path)) {
        throw codedError('ROLLBACK_BACKUP_NOT_FOUND', `Backup not found: ${backup.path}`);
      }
      const target = resolveSafePath(snapshot.project_root, backup.path);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(backup.backup_path, target);
      restored.push(backup.path);
    }
    const rolledBackAt = new Date().toISOString();
    writeJson(path.join(snapshot.sandbox_path, 'logs', `rollback-${Date.now()}.json`), {
      run_id: runId,
      restored_files: restored,
      rolled_back_at: rolledBackAt,
    });
    return {
      run_id: runId,
      restored_files: restored,
      rolled_back_at: rolledBackAt,
    };
  } finally {
    lockManager.release(runId);
  }
}

export function generateUnifiedDiff(oldText: string, newText: string, diffPath: string): string {
  if (oldText === newText) return '';
  const oldLines = splitLines(oldText);
  const newLines = splitLines(newText);
  const lines = [
    `--- a/${diffPath}`,
    `+++ b/${diffPath}`,
    `@@ -1,${oldLines.length} +1,${newLines.length} @@`,
    ...oldLines.map((line) => `-${line}`),
    ...newLines.map((line) => `+${line}`),
  ];
  return lines.join('\n');
}

function normalizeSourceFiles(sourceFiles: string[]): string[] {
  return sourceFiles.map(normalizeRelativePath);
}

function assertAllowedFile(project: Project, relativePath: string): {
  relativePath: string;
  absPath: string;
  size: number;
  mtimeMs: number;
} {
  if (!matchesAny(project.allowed_paths, relativePath)) {
    throw codedError('PATH_NOT_ALLOWED', `Path is outside allowed_paths: ${relativePath}`);
  }
  if (matchesAny(project.blocked_paths, relativePath)) {
    throw codedError('PATH_NOT_ALLOWED', `Path is blocked: ${relativePath}`);
  }
  const absPath = resolveSafePath(project.project_root, relativePath);
  if (!fs.existsSync(absPath)) {
    throw codedError('SOURCE_FILE_NOT_FOUND', `Source file not found: ${relativePath}`);
  }
  const stat = fs.lstatSync(absPath);
  if (stat.isSymbolicLink()) {
    throw codedError('PATH_NOT_ALLOWED', `Symlink source file is not allowed: ${relativePath}`);
  }
  if (!stat.isFile()) {
    throw codedError('PATH_NOT_ALLOWED', `Source path is not a file: ${relativePath}`);
  }
  return {
    relativePath,
    absPath,
    size: stat.size,
    mtimeMs: stat.mtimeMs,
  };
}

function normalizeRelativePath(input: string): string {
  const normalized = input.trim().replaceAll('\\', '/').replace(/^\.\//, '').replace(/\/+/g, '/');
  if (
    normalized.length === 0
    || normalized.includes('\0')
    || path.isAbsolute(normalized)
    || normalized.split('/').some((segment) => segment === '..')
  ) {
    throw codedError('PATH_NOT_ALLOWED', `Invalid source path: ${input}`);
  }
  return normalized;
}

function matchesAny(patterns: string[], relativePath: string): boolean {
  return patterns.some((pattern) => matchesPattern(pattern, relativePath));
}

function matchesPattern(pattern: string, relativePath: string): boolean {
  const normalizedPattern = normalizePattern(pattern);
  if (normalizedPattern === relativePath) return true;
  if (normalizedPattern.endsWith('/**')) {
    const prefix = normalizedPattern.slice(0, -3);
    return relativePath === prefix || relativePath.startsWith(`${prefix}/`);
  }
  if (normalizedPattern.includes('*')) {
    let regex = '';
    for (let index = 0; index < normalizedPattern.length; index += 1) {
      const char = normalizedPattern[index] ?? '';
      const next = normalizedPattern[index + 1] ?? '';
      if (char === '*' && next === '*') {
        regex += '.*';
        index += 1;
      } else if (char === '*') {
        regex += '[^/]*';
      } else {
        regex += char.replace(/[.+?^${}()|[\]\\]/g, '\\$&');
      }
    }
    return new RegExp(`^${regex}$`).test(relativePath);
  }
  return false;
}

function normalizePattern(pattern: string): string {
  return pattern.trim().replaceAll('\\', '/').replace(/^\.\//, '').replace(/\/+/g, '/');
}

function sandboxRoot(projectRoot: string, runId: string): string {
  return path.join(projectRoot, '.agentmesh', 'runs', runId);
}

function snapshotPath(sandboxPath: string): string {
  return path.join(sandboxPath, 'snapshot.json');
}

function loadSnapshot(projectRoot: string, runId: string): SandboxSnapshot {
  const sandboxPath = sandboxRoot(projectRoot, runId);
  const snapshotFile = snapshotPath(sandboxPath);
  if (!fs.existsSync(snapshotFile)) {
    throw codedError('SANDBOX_NOT_FOUND', `Sandbox not found for run: ${runId}`);
  }
  return readJson<SandboxSnapshot>(snapshotFile);
}

function assertSnapshotClean(snapshot: SandboxSnapshot, changedFiles: string[]): void {
  const changed = new Set(changedFiles);
  for (const entry of snapshot.source_files) {
    if (!changed.has(entry.path)) continue;
    const current = resolveSafePath(snapshot.project_root, entry.path);
    if (!fs.existsSync(current)) {
      throw codedError('SANDBOX_DIRTY', `Project file disappeared: ${entry.path}`);
    }
    const currentHash = hashFile(current);
    if (currentHash !== entry.hash) {
      throw codedError('SANDBOX_DIRTY', `Project file changed since sandbox init: ${entry.path}`);
    }
  }
}

function createBackups(
  snapshot: SandboxSnapshot,
  changedFiles: string[],
  appliedAt: string,
): BackupEntry[] {
  const timestamp = appliedAt.replace(/[-:.TZ]/g, '');
  return changedFiles.map((relativePath) => {
    const source = resolveSafePath(snapshot.project_root, relativePath);
    const backupPath = path.join(
      snapshot.sandbox_path,
      'backups',
      `${relativePath}.bak.${timestamp}`,
    );
    fs.mkdirSync(path.dirname(backupPath), { recursive: true });
    fs.copyFileSync(source, backupPath);
    const stat = fs.statSync(source);
    return {
      path: relativePath,
      backup_path: backupPath,
      hash: hashFile(source),
      size: stat.size,
    };
  });
}

function writePatch(sandboxPath: string, patch: string): void {
  const patchesDir = path.join(sandboxPath, 'patches');
  fs.mkdirSync(patchesDir, { recursive: true });
  const seq = fs.readdirSync(patchesDir).filter((file) => file.endsWith('.patch')).length + 1;
  fs.writeFileSync(path.join(patchesDir, `${String(seq).padStart(3, '0')}.patch`), patch, 'utf8');
}

function hashFile(filePath: string): string {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function readTextIfExists(filePath: string): string {
  if (!fs.existsSync(filePath)) return '';
  return fs.readFileSync(filePath, 'utf8');
}

function splitLines(content: string): string[] {
  if (content.length === 0) return [];
  return content.replace(/\n$/, '').split(/\r?\n/);
}

function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, 'utf8')) as T;
}

function writeJson(filePath: string, value: unknown): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(value, null, 2), 'utf8');
}

function codedError(code: string, message: string): Error & { code: string } {
  const error = new Error(message) as Error & { code: string };
  error.code = code;
  return error;
}
