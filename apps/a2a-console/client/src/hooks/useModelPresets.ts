import { useMemo } from 'react';

import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';

export interface ModelPresetEntry {
  agent: string;
  model: string | null;
  source: 'override' | 'default';
}

interface RawModelPresets {
  overrides: Record<string, string | null>;
  defaults: Record<string, string | null>;
}

const AGENT_ORDER = ['pm', 'architect', 'developer', 'qa', 'controller', 'risk'];

function flatten(raw: RawModelPresets): { entries: ModelPresetEntry[] } {
  const entries: ModelPresetEntry[] = [];
  for (const agent of AGENT_ORDER) {
    const override = raw.overrides[agent] ?? null;
    const def = raw.defaults[agent] ?? null;
    entries.push({
      agent,
      model: override ?? def,
      source: override ? 'override' : 'default',
    });
  }
  return { entries };
}

export function useModelPresets(_taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  const result = usePolling<RawModelPresets>(
    () => apiGet('/api/a2a/model-presets'),
    [],
    { intervalMs: Math.max(interval, 10_000) },
  );
  const data = useMemo(() => (result.data ? flatten(result.data) : null), [result.data]);
  return { ...result, data };
}
