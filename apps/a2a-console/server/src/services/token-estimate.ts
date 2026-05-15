export const CHARS_PER_TOKEN = 3.5;

export function estimateTokens(chars: number): number {
  return Math.ceil(chars / CHARS_PER_TOKEN);
}

export interface AgentTokenBucket {
  pm: number;
  architect: number;
  developer: number;
  qa: number;
  controller: number;
  human: number;
}

export function emptyAgentBucket(): AgentTokenBucket {
  return { pm: 0, architect: 0, developer: 0, qa: 0, controller: 0, human: 0 };
}
