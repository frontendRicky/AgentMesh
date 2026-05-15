import { metricsResponseSchema, type MetricsResponse } from '@a2a-console/contract';

import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';

export function useMetrics(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<MetricsResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/metrics`, metricsResponseSchema),
    [taskId ?? ''],
    { intervalMs: Math.max(interval, 10_000), enabled: Boolean(taskId) },
  );
}
