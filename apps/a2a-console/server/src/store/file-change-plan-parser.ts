const FORBIDDEN_HEADING_RE = /^#{1,6}\s+.*(forbidden|禁改|non[- ]authorization)/i;
const ANY_HEADING_RE = /^#{1,6}\s+/;
const TABLE_PATH_RE = /^\|\s*`([^`]+)`\s*\|\s*([^|]*?)\s*\|/;

/**
 * 从 file-change-plan.md 提取"将被修改"的路径列表。
 * 跳过两类内容：
 *   1. forbidden / 禁改 / non-authorization 段落下的全部表格
 *   2. 任何表格行中第二列 operation == 'forbidden' 的行（双保险）
 */
export function parseFileChangePlanPaths(content: string): string[] {
  try {
    const paths = new Set<string>();
    let inForbiddenSection = false;
    for (const line of content.split(/\r?\n/)) {
      if (ANY_HEADING_RE.test(line)) {
        inForbiddenSection = FORBIDDEN_HEADING_RE.test(line);
        continue;
      }
      if (inForbiddenSection) continue;
      const match = line.match(TABLE_PATH_RE);
      if (!match?.[1]) continue;
      const operation = (match[2] ?? '').trim().toLowerCase();
      if (operation === 'forbidden') continue;
      paths.add(match[1]);
    }
    return Array.from(paths);
  } catch {
    return [];
  }
}
