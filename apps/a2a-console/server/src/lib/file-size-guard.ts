import fs from 'node:fs';

export const MAX_FULL_READ_BYTES = 500 * 1024;
export const TRUNCATE_TO_BYTES = 100 * 1024;

export interface ReadResult {
  body: string;
  size: number;
  truncated: boolean;
}

export function readMarkdownWithLimit(absPath: string): ReadResult {
  const stat = fs.statSync(absPath);
  if (stat.size <= MAX_FULL_READ_BYTES) {
    return { body: fs.readFileSync(absPath, 'utf8'), size: stat.size, truncated: false };
  }
  const fd = fs.openSync(absPath, 'r');
  try {
    const buf = Buffer.alloc(TRUNCATE_TO_BYTES);
    fs.readSync(fd, buf, 0, TRUNCATE_TO_BYTES, 0);
    return { body: buf.toString('utf8'), size: stat.size, truncated: true };
  } finally {
    fs.closeSync(fd);
  }
}
