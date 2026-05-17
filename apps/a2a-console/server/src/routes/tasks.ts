import { existsSync, lstatSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path, { join, relative, sep } from 'node:path';
import zlib from 'node:zlib';

import { Router } from 'express';
import type { Response } from 'express';

import { fail, ok, resolveProjectRoot, handleReaderError, validateTaskIdParam } from './_helpers.js';
import { resolveSafePath } from '../lib/path-guard.js';

export const tasksRouter = Router();

const TASK_PACKAGE_MAX_BYTES = 50 * 1024 * 1024;

type RuntimeZlib = typeof zlib & {
  crc32?: (data: Buffer, value?: number) => number;
};

interface TaskFile {
  absPath: string;
  zipPath: string;
}

interface ZipFile extends TaskFile {
  data: Buffer;
}

interface ZipEntry extends ZipFile {
  crc: number;
  localHeaderOffset: number;
}

tasksRouter.use((req, res, next) => {
  const rawPath = req.originalUrl ?? req.url ?? '';
  const decoded = (() => {
    try {
      return decodeURIComponent(rawPath);
    } catch {
      return rawPath;
    }
  })();
  if (decoded.includes('..')) {
    fail(res, 400, 'TASK_ID_INVALID', 'Task ID contains invalid characters');
    return;
  }
  next();
});

tasksRouter.get('/', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  try {
    const status = typeof req.query['status'] === 'string' ? req.query['status'] : undefined;
    const agent = typeof req.query['agent'] === 'string' ? req.query['agent'] : undefined;
    const priority = typeof req.query['priority'] === 'string' ? req.query['priority'] : undefined;
    const q = typeof req.query['q'] === 'string' ? req.query['q'] : undefined;
    const items = ctx.reader.listTasks({ status, agent, priority, q });
    ok(res, { total: items.length, items });
  } catch (e) {
    handleReaderError(res, e);
  }
});

tasksRouter.get('/:taskId/download', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;

  try {
    const taskDir = path.join(ctx.projectRoot, '.ai-agents', 'workspace', taskId);
    const safeTaskDir = resolveSafePath(ctx.projectRoot, `.ai-agents/workspace/${taskId}`);
    if (!existsSync(safeTaskDir) || !statSync(safeTaskDir).isDirectory()) {
      return fail(res, 404, 'TASK_NOT_FOUND', `Task not found: ${taskId}`);
    }

    const files = collectTaskFiles(safeTaskDir);
    const totalBytes = files.reduce((sum, file) => sum + statSync(file.absPath).size, 0);
    if (totalBytes > TASK_PACKAGE_MAX_BYTES) {
      return fail(
        res,
        400,
        'TASK_PACKAGE_TOO_LARGE',
        `任务包超过 50 MB，请直接到 ${taskDir} 目录手动复制文件。`,
      );
    }

    const zipFiles = files.map((file) => ({ ...file, data: readFileSync(file.absPath) }));
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${taskId}.zip"`);
    res.setHeader('Transfer-Encoding', 'chunked');
    writeZip(res, zipFiles);
  } catch (e) {
    handleReaderError(res, e);
  }
});

function collectTaskFiles(taskDir: string): TaskFile[] {
  const files: TaskFile[] = [];

  function walk(dir: string): void {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const absPath = join(dir, entry.name);
      const stat = lstatSync(absPath);
      if (stat.isSymbolicLink()) continue;
      if (stat.isDirectory()) {
        walk(absPath);
        continue;
      }
      if (!stat.isFile()) continue;
      files.push({
        absPath,
        zipPath: relative(taskDir, absPath).split(sep).join('/'),
      });
    }
  }

  walk(taskDir);
  return files;
}

function writeZip(res: Response, files: ZipFile[]): void {
  const crc32 = (zlib as RuntimeZlib).crc32;
  if (typeof crc32 !== 'function') {
    throw new Error('node:zlib.crc32 is required for ZIP STORE streaming');
  }

  let offset = 0;
  const entries: ZipEntry[] = files.map((file) => ({
    ...file,
    crc: crc32(file.data, 0) >>> 0,
    localHeaderOffset: 0,
  }));

  for (const entry of entries) {
    entry.localHeaderOffset = offset;
    const localHeader = createLocalFileHeader(entry);
    res.write(localHeader);
    res.write(entry.data);
    offset += localHeader.length + entry.data.length;
  }

  const centralDirOffset = offset;
  const centralDirectory = entries.map(createCentralDirectoryHeader);
  for (const header of centralDirectory) {
    res.write(header);
    offset += header.length;
  }

  res.end(createEndOfCentralDirectory(entries.length, offset - centralDirOffset, centralDirOffset));
}

function createLocalFileHeader(entry: ZipEntry): Buffer {
  const fileName = Buffer.from(entry.zipPath, 'utf8');
  const header = Buffer.alloc(30 + fileName.length);
  header.writeUInt32LE(0x04034b50, 0);
  header.writeUInt16LE(20, 4);
  header.writeUInt16LE(0, 6);
  header.writeUInt16LE(0, 8);
  header.writeUInt16LE(0, 10);
  header.writeUInt16LE(0, 12);
  header.writeUInt32LE(entry.crc, 14);
  header.writeUInt32LE(entry.data.length, 18);
  header.writeUInt32LE(entry.data.length, 22);
  header.writeUInt16LE(fileName.length, 26);
  header.writeUInt16LE(0, 28);
  fileName.copy(header, 30);
  return header;
}

function createCentralDirectoryHeader(entry: ZipEntry): Buffer {
  const fileName = Buffer.from(entry.zipPath, 'utf8');
  const header = Buffer.alloc(46 + fileName.length);
  header.writeUInt32LE(0x02014b50, 0);
  header.writeUInt16LE(20, 4);
  header.writeUInt16LE(20, 6);
  header.writeUInt16LE(0, 8);
  header.writeUInt16LE(0, 10);
  header.writeUInt16LE(0, 12);
  header.writeUInt16LE(0, 14);
  header.writeUInt32LE(entry.crc, 16);
  header.writeUInt32LE(entry.data.length, 20);
  header.writeUInt32LE(entry.data.length, 24);
  header.writeUInt16LE(fileName.length, 28);
  header.writeUInt16LE(0, 30);
  header.writeUInt16LE(0, 32);
  header.writeUInt16LE(0, 34);
  header.writeUInt16LE(0, 36);
  header.writeUInt32LE(0, 38);
  header.writeUInt32LE(entry.localHeaderOffset, 42);
  fileName.copy(header, 46);
  return header;
}

function createEndOfCentralDirectory(
  fileCount: number,
  centralDirSize: number,
  centralDirOffset: number,
): Buffer {
  const header = Buffer.alloc(22);
  header.writeUInt32LE(0x06054b50, 0);
  header.writeUInt16LE(0, 4);
  header.writeUInt16LE(0, 6);
  header.writeUInt16LE(fileCount, 8);
  header.writeUInt16LE(fileCount, 10);
  header.writeUInt32LE(centralDirSize, 12);
  header.writeUInt32LE(centralDirOffset, 16);
  header.writeUInt16LE(0, 20);
  return header;
}
