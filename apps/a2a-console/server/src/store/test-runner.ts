import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import type { TestResult, TestSuite } from '@a2a-console/contract';

import type { Project } from './project-registry.js';
import { runPool } from './run-pool.js';

const PACKAGE_MANAGER = 'npm';
const TOOLCHAIN_NAME = 'nodejs';
const TEST_TIMEOUT_MS = 30000;
const MAX_LOG_CHARS = 1024 * 1024;
const SUMMARY_LINES = 50;

export async function runTestSuites(
  runId: string,
  project: Project,
  suites: TestSuite[],
): Promise<TestResult[]> {
  const scripts = readPackageScripts(project.project_root);
  const results: TestResult[] = [];
  for (const suite of suites) {
    if (typeof scripts[suite] !== 'string') {
      throw codedError('TEST_SCRIPT_NOT_FOUND', `package.json script not found: ${suite}`);
    }
    results.push(await runSuite(runId, project.project_root, suite));
  }
  updateRunTestResult(runId, results);
  writeJson(path.join(testResultsDir(project.project_root, runId), 'latest.json'), {
    run_id: runId,
    project_id: project.project_id,
    results,
  });
  return results;
}

export function readTestResults(project: Project, runId: string): TestResult[] {
  const filePath = path.join(testResultsDir(project.project_root, runId), 'latest.json');
  if (!fs.existsSync(filePath)) return [];
  const parsed = JSON.parse(fs.readFileSync(filePath, 'utf8')) as { results?: unknown };
  return Array.isArray(parsed.results) ? parsed.results.filter(isTestResult) : [];
}

function runSuite(runId: string, projectRoot: string, suite: TestSuite): Promise<TestResult> {
  return new Promise((resolve) => {
    const startedAt = Date.now();
    const child = spawn(PACKAGE_MANAGER, ['run', suite], {
      cwd: projectRoot,
      shell: false,
      env: process.env,
    });
    let stdout = '';
    let stderr = '';
    let settled = false;

    const timeout = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill('SIGTERM');
      setTimeout(() => {
        if (!child.killed) child.kill('SIGKILL');
      }, 1000);
      resolve(finishResult(runId, projectRoot, suite, 'timeout', -1, startedAt, stdout, stderr));
    }, TEST_TIMEOUT_MS);

    child.stdout.on('data', (chunk: Buffer) => {
      stdout = appendLog(stdout, chunk.toString('utf8'));
    });
    child.stderr.on('data', (chunk: Buffer) => {
      stderr = appendLog(stderr, chunk.toString('utf8'));
    });
    child.on('error', (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      stderr = appendLog(stderr, error.message);
      resolve(finishResult(runId, projectRoot, suite, 'fail', 1, startedAt, stdout, stderr));
    });
    child.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      resolve(finishResult(
        runId,
        projectRoot,
        suite,
        code === 0 ? 'pass' : 'fail',
        code ?? 1,
        startedAt,
        stdout,
        stderr,
      ));
    });
  });
}

function finishResult(
  runId: string,
  projectRoot: string,
  suite: TestSuite,
  status: TestResult['status'],
  exitCode: number,
  startedAt: number,
  stdout: string,
  stderr: string,
): TestResult {
  const createdAt = new Date().toISOString();
  const logPath = path.join(logsDir(projectRoot, runId), `${suite}-${Date.now()}.log`);
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  fs.writeFileSync(logPath, truncateLog(`STDOUT\n${stdout}\n\nSTDERR\n${stderr}`), 'utf8');
  return {
    suite,
    status,
    exit_code: exitCode,
    duration_ms: Date.now() - startedAt,
    summary_lines: summaryLines(stderr || stdout),
    log_path: logPath,
    toolchain: TOOLCHAIN_NAME,
    created_at: createdAt,
  };
}

function readPackageScripts(projectRoot: string): Record<string, unknown> {
  const packageJsonPath = path.join(projectRoot, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    throw codedError('PACKAGE_JSON_NOT_FOUND', 'package.json not found');
  }
  const parsed = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8')) as { scripts?: unknown };
  if (parsed.scripts === null || typeof parsed.scripts !== 'object') {
    return {};
  }
  return parsed.scripts as Record<string, unknown>;
}

function updateRunTestResult(runId: string, results: TestResult[]): void {
  const last = results[results.length - 1];
  const lastTestResult = results.some((result) => result.status === 'timeout')
    ? 'timeout'
    : results.some((result) => result.status === 'fail')
      ? 'fail'
      : 'pass';
  runPool.update(runId, {
    last_test_run_at: last?.created_at ?? new Date().toISOString(),
    last_test_result: lastTestResult,
  });
}

function testResultsDir(projectRoot: string, runId: string): string {
  return path.join(projectRoot, '.agentmesh', 'runs', runId, 'test-results');
}

function logsDir(projectRoot: string, runId: string): string {
  return path.join(projectRoot, '.agentmesh', 'runs', runId, 'logs');
}

function appendLog(current: string, next: string): string {
  return truncateLog(current + next);
}

function truncateLog(value: string): string {
  return value.length > MAX_LOG_CHARS ? value.slice(0, MAX_LOG_CHARS) : value;
}

function summaryLines(content: string): string[] {
  return content.split(/\r?\n/).filter(Boolean).slice(0, SUMMARY_LINES);
}

function writeJson(filePath: string, value: unknown): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(value, null, 2), 'utf8');
}

function isTestResult(value: unknown): value is TestResult {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    isSuite(record['suite'])
    && isStatus(record['status'])
    && typeof record['exit_code'] === 'number'
    && typeof record['duration_ms'] === 'number'
    && Array.isArray(record['summary_lines'])
    && record['summary_lines'].every((line) => typeof line === 'string')
    && typeof record['log_path'] === 'string'
    && typeof record['toolchain'] === 'string'
    && typeof record['created_at'] === 'string'
  );
}

function isSuite(value: unknown): value is TestSuite {
  return value === 'typecheck' || value === 'lint' || value === 'build';
}

function isStatus(value: unknown): value is TestResult['status'] {
  return value === 'pass' || value === 'fail' || value === 'timeout';
}

function codedError(code: string, message: string): Error & { code: string } {
  const error = new Error(message) as Error & { code: string };
  error.code = code;
  return error;
}
