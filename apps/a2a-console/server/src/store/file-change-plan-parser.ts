export function parseFileChangePlanPaths(content: string): string[] {
  try {
    const paths = new Set<string>();
    for (const line of content.split(/\r?\n/)) {
      const match = line.match(/^\|\s*`([^`]+)`\s*\|/);
      if (!match?.[1]) continue;
      paths.add(match[1]);
    }
    return Array.from(paths);
  } catch {
    return [];
  }
}
