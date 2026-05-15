// Last updated: 2026-05-15. Approximate values; UI copy already disclaims as estimate.
export const MODEL_CONTEXT: Record<string, number> = {
  'gpt-5.5': 200_000,
  'gpt-5.5-mini': 128_000,
  'claude-4.6-sonnet-medium-thinking': 200_000,
  'claude-opus-4-7-thinking-high': 200_000,
  'claude-opus-4-7-thinking-medium': 200_000,
  'claude-4.6-opus-medium-thinking': 200_000,
  'gpt-5.3-codex': 128_000,
  'kimi-k2.5': 200_000,
  'composer-2-fast': 128_000,
};

export const DEFAULT_CONTEXT = 200_000;

export function modelMaxContext(model: string | null | undefined): number {
  if (!model) return DEFAULT_CONTEXT;
  return MODEL_CONTEXT[model] ?? DEFAULT_CONTEXT;
}

export const MODEL_OPTIONS: { slug: string; label: string }[] = [
  { slug: 'gpt-5.5', label: 'gpt-5.5 (高推理 / Codex)' },
  { slug: 'gpt-5.5-mini', label: 'gpt-5.5-mini (低成本)' },
  { slug: 'claude-4.6-sonnet-medium-thinking', label: 'claude-4.6 sonnet (中推理 / 中成本)' },
  { slug: 'claude-opus-4-7-thinking-high', label: 'claude-opus 4.7 high (高推理)' },
  { slug: 'claude-opus-4-7-thinking-medium', label: 'claude-opus 4.7 medium' },
];
