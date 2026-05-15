export const CHARS_PER_TOKEN = 3.5;

export function estimateTokens(chars: number): number {
  return Math.ceil(chars / CHARS_PER_TOKEN);
}
