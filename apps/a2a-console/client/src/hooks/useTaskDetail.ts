import { useMemo } from 'react';
import { taskDetailResponseSchema, type TaskDetailResponse } from '@a2a-console/contract';

import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { StateFrontmatter } from '@/types/state';
import type { TaskFrontmatter } from '@/types/task';

export interface TaskDetailData {
  task: TaskFrontmatter & Record<string, unknown>;
  state: StateFrontmatter & Record<string, unknown>;
  task_body: string;
  state_body: string;
  task_parse_error: string | null;
  state_parse_error: string | null;
}

function flatten(raw: TaskDetailResponse): TaskDetailData {
  return {
    task: (raw.task.frontmatter ?? {}) as TaskDetailData['task'],
    state: (raw.state.frontmatter ?? {}) as TaskDetailData['state'],
    task_body: raw.task.body ?? '',
    state_body: raw.state.body ?? '',
    task_parse_error: raw.task.parse_error,
    state_parse_error: raw.state.parse_error,
  };
}

export function useTaskDetail(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  const result = usePolling<TaskDetailResponse>(
    () => apiGet(`/api/a2a/tasks/${taskId}`, taskDetailResponseSchema),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
  const data = useMemo(() => (result.data ? flatten(result.data) : null), [result.data]);
  return { ...result, data };
}
