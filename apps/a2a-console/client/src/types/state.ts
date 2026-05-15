export type AgentRole =
  | 'pm'
  | 'architect'
  | 'developer'
  | 'qa'
  | 'controller'
  | 'human'
  | 'none';

export type CurrentStatus =
  | 'created'
  | 'pm_processing'
  | 'pm_completed'
  | 'architect_processing'
  | 'architect_completed'
  | 'human_review_required'
  | 'developer_processing'
  | 'developer_completed'
  | 'qa_processing'
  | 'qa_completed'
  | 'final_review_required'
  | 'completed'
  | 'blocked'
  | 'cancelled';

export type ReviewStatus = 'not_required' | 'pending' | 'approved' | 'rejected';

export interface StateFrontmatter {
  task_id: string;
  current_status: CurrentStatus;
  previous_status: CurrentStatus;
  current_agent: AgentRole;
  next_agent: AgentRole;
  allowed_next_statuses: CurrentStatus[];
  human_review_status: ReviewStatus;
  final_review_status: ReviewStatus;
  produced_artifacts: string[];
  active_blocker: string | null;
  blockers_history: string[];
  blocked_context: Record<string, unknown> | null;
  updated_at: string;
  schema_version: string;
}
