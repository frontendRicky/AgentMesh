import type { MessageItem as ContractMessageItem } from '@a2a-console/contract';

export type MessageType =
  | 'request'
  | 'response'
  | 'handoff'
  | 'review'
  | 'blocker'
  | 'gate_failure'
  | 'status'
  | 'final';

export type MessageItem = ContractMessageItem & {
  message_type: MessageType | string | null;
};
