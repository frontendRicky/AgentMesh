import { useEffect, useState } from 'react';

import { apiGet, type ApiError, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { ArtifactFile, TreeNode } from '@/types/artifact';

interface ArtifactsTreeResponse {
  artifact_count?: number;
  total_size?: number;
  tree: TreeNode[];
}

export function useArtifactsTree(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<ArtifactsTreeResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}/artifacts`),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}

export function useArtifactFile(taskId: string | null, relPath: string | null) {
  const [data, setData] = useState<ArtifactFile | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!taskId || !relPath) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    apiGet<ArtifactFile>(
      `/api/a2a/tasks/${taskId}/artifacts?path=${encodeURIComponent(relPath)}`,
    )
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e as ApiError);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [taskId, relPath]);

  return { data, error, loading };
}
