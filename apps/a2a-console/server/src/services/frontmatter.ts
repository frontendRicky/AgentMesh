import matter from 'gray-matter';

export interface ParsedMarkdown<TFrontmatter = Record<string, unknown>> {
  frontmatter: TFrontmatter | null;
  body: string;
  parse_error: string | null;
}

export function parseMarkdown<T = Record<string, unknown>>(raw: string): ParsedMarkdown<T> {
  try {
    const parsed = matter(raw);
    return {
      frontmatter: (parsed.data ?? null) as T | null,
      body: parsed.content,
      parse_error: null,
    };
  } catch (e) {
    return {
      frontmatter: null,
      body: raw,
      parse_error: e instanceof Error ? e.message : String(e),
    };
  }
}
