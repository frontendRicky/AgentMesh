import { useMemo } from 'react';

import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { StateFrontmatter } from '@/types/state';
import type { TaskFrontmatter } from '@/types/task';

interface ParsedMarkdown {
  frontmatter: Record<string, unknown> | null;
  body: string;
  parse_error: string | null;
}

interface TaskDetailRaw {
  task: ParsedMarkdown;
  state: ParsedMarkdown;
  summary: unknown;
}

export interface TaskDetailData {
  task: TaskFrontmatter & Record<string, unknown>;
  state: StateFrontmatter & Record<string, unknown>;
  task_body: string;
  state_body: string;
  task_parse_error: string | null;
  state_parse_error: string | null;
}

function flatten(raw: TaskDetailRaw): TaskDetailData {
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
  const result = usePolling<TaskDetailRaw>(
    () => apiGet<TaskDetailRaw>(`/api/a2a/tasks/${taskId}`),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
  const data = useMemo(() => (result.data ? flatten(result.data) : null), [result.data]);
  return { ...result, data };
}
