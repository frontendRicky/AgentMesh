export type TaskType =
  | 'feature'
  | 'refactor'
  | 'bugfix'
  | 'ui-redesign'
  | 'permission'
  | 'api-integration';

export type Priority = 'P0' | 'P1' | 'P2';

export interface TaskScope {
  in_scope: string[];
  out_of_scope: string[];
}

export interface TaskFrontmatter {
  task_id: string;
  task_type: TaskType;
  task_title: string;
  created_by: string;
  human_owner: string;
  priority: Priority;
  scope: TaskScope;
  constraints: string[];
  initial_input_messages?: string[];
  required_artifacts: string[];
  created_at: string;
  schema_version: string;
}

export interface TaskListItem {
  task_id: string;
  task_title: string | null;
  task_type: string | null;
  priority: string | null;
  current_status: string | null;
  current_agent: string | null;
  human_review_status: string | null;
  final_review_status: string | null;
  blocker_count: number;
  produced_artifacts_count: number;
  token_total_estimate: number;
  created_at: string | null;
  updated_at: string | null;
}
