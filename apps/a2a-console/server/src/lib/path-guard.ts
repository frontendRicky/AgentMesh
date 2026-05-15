import fs from 'node:fs';
import path from 'node:path';

export class PathTraversalError extends Error {
  code = 'PATH_TRAVERSAL';
  constructor(detail: string) {
    super(`Path traversal blocked: ${detail}`);
  }
}

export class ProjectRootInvalidError extends Error {
  code = 'PROJECT_ROOT_INVALID';
  constructor(detail: string) {
    super(`Invalid project root: ${detail}`);
  }
}

/**
 * 校验 root 是合法 project root：
 *  - 必须是绝对路径
 *  - 必须存在
 *  - 必须包含 .ai-agents/workspace 子目录
 * 返回 realpath。
 */
export function validateProjectRoot(rawRoot: string): string {
  if (!rawRoot || !path.isAbsolute(rawRoot)) {
    throw new ProjectRootInvalidError('must be an absolute path');
  }
  let real: string;
  try {
    real = fs.realpathSync(rawRoot);
  } catch {
    throw new ProjectRootInvalidError('directory does not exist');
  }
  const stat = fs.statSync(real);
  if (!stat.isDirectory()) {
    throw new ProjectRootInvalidError('not a directory');
  }
  const workspace = path.join(real, '.ai-agents', 'workspace');
  if (!fs.existsSync(workspace)) {
    throw new ProjectRootInvalidError('missing .ai-agents/workspace');
  }
  return real;
}

/**
 * 把 requested 视为相对 root 的子路径，realpath 后必须仍位于 root 内。
 *  - 拒绝绝对路径
 *  - 拒绝包含 .. 段
 *  - realpath 后 startsWith(realRoot + sep)，否则视为越界（含 symlink 攻击）
 *  - 拒绝路径中含 null byte（Node 原生会抛，这里防御）
 */
export function resolveSafePath(root: string, requested: string): string {
  if (requested.includes('\0')) {
    throw new PathTraversalError('null byte in path');
  }
  if (path.isAbsolute(requested)) {
    throw new PathTraversalError('absolute path not allowed');
  }
  const segments = requested.split(/[\\/]+/);
  if (segments.some((s) => s === '..')) {
    throw new PathTraversalError('".." segment not allowed');
  }
  const realRoot = fs.realpathSync(root);
  const joined = path.resolve(realRoot, requested);
  let realJoined: string;
  try {
    realJoined = fs.realpathSync(joined);
  } catch {
    // 文件不存在时也校验目录的 realpath
    const dir = path.dirname(joined);
    const realDir = fs.realpathSync(dir);
    if (realDir !== realRoot && !realDir.startsWith(realRoot + path.sep)) {
      throw new PathTraversalError('parent dir escapes project root');
    }
    return joined;
  }
  if (realJoined !== realRoot && !realJoined.startsWith(realRoot + path.sep)) {
    throw new PathTraversalError('symlink escapes project root');
  }
  return realJoined;
}
