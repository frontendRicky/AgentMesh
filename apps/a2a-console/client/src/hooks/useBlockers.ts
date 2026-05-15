import { reviewsResponseSchema, type ReviewsResponse } from '@a2a-console/contract';

import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { BlockersResponse } from '@/types/blocker';

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
  return usePolling<ReviewsResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/reviews`, reviewsResponseSchema),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}
