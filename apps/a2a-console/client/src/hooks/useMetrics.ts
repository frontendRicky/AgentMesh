import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';

export interface MetricsResponse {
  tokens: {
    total_estimate: number;
    by_agent: Record<string, number>;
    by_stage: Record<string, number>;
  };
  context: {
    active_chars: number;
    active_tokens_estimate: number;
    model: string | null;
    model_max_context: number;
    usage_pct: number;
    level: 'safe' | 'warning' | 'high' | 'danger';
  };
}

export function useMetrics(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<MetricsResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/metrics`),
    [taskId ?? ''],
    { intervalMs: Math.max(interval, 10_000), enabled: Boolean(taskId) },
  );
}
