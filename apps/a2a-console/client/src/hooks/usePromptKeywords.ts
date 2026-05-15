import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';

export interface PromptKeywordResponse {
  current_status: string;
  keyword: string | null;
  cli_command?: string | null;
  ui_action: 'copy' | 'show_only' | 'link';
  cli_role: string | null;
  hint?: string | null;
  model_recommended?: string | null;
}

export function usePromptKeywords(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<PromptKeywordResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/prompt-keywords`),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}
