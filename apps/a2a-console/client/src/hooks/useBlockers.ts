import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { BlockersResponse, ReviewItem } from '@/types/blocker';

export function useBlockers(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<BlockersResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/blockers`),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}

export function useReviews(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<{ items: ReviewItem[] }>(
    () => apiGet(`/api/a2a/tasks/${taskId}/human-reviews`),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}
