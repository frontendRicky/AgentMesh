import { messagesResponseSchema, type MessagesResponse } from '@a2a-console/contract';

import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';

export function useMessages(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<MessagesResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/messages`, messagesResponseSchema),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}
