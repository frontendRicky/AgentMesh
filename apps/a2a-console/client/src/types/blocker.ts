import type { ReviewItem as ContractReviewItem } from '@a2a-console/contract';

export interface BlockerItem {
  blocker_id: string | null;
  blocking_reason: string | null;
  missing_artifacts: string[];
  required_fix: string | null;
  resume_to_agent: string | null;
  resume_to_status: string | null;
  created_at: string | null;
  file_path: string;
}

export interface BlockersResponse {
  active_blocker: string | null;
  blocked_context: Record<string, unknown> | null;
  blockers_history: string[];
  items: BlockerItem[];
}

export type ReviewItem = ContractReviewItem & {
  verdict: 'approved' | 'rejected' | 'needs_changes' | string | null;
};
