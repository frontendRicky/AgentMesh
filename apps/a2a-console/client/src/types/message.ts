export type MessageType =
  | 'request'
  | 'response'
  | 'handoff'
  | 'review'
  | 'blocker'
  | 'gate_failure'
  | 'status'
  | 'final';

export interface MessageItem {
  message_id: string | null;
  from_agent: string | null;
  to_agent: string | null;
  message_type: MessageType | string | null;
  intent: string | null;
  summary: string | null;
  referenced_artifacts: string[];
  created_at: string | null;
  file_path: string;
}
