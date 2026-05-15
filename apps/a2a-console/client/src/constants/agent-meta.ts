export type AgentId = 'controller' | 'pm' | 'architect' | 'developer' | 'qa' | 'human';

export interface AgentMeta {
  id: AgentId;
  name: string;
  emoji: string;
  bubbleClass: string;
  ringClass: string;
  badgeClass: string;
  hint: string;
}

export const AGENTS: Record<AgentId, AgentMeta> = {
  controller: {
    id: 'controller',
    name: 'Controller',
    emoji: '🎛️',
    bubbleClass: 'bg-purple-50 border-purple-200',
    ringClass: 'ring-purple-300 bg-purple-100 text-purple-700',
    badgeClass: 'bg-purple-100 text-purple-700',
    hint: '调度状态机，管 state.md 推进',
  },
  pm: {
    id: 'pm',
    name: 'PM',
    emoji: '📋',
    bubbleClass: 'bg-orange-50 border-orange-200',
    ringClass: 'ring-orange-300 bg-orange-100 text-orange-700',
    badgeClass: 'bg-orange-100 text-orange-700',
    hint: '拆需求，出 PRD / task-breakdown',
  },
  architect: {
    id: 'architect',
    name: 'Architect',
    emoji: '🏛️',
    bubbleClass: 'bg-sky-50 border-sky-200',
    ringClass: 'ring-sky-300 bg-sky-100 text-sky-700',
    badgeClass: 'bg-sky-100 text-sky-700',
    hint: '出技术方案 / file-change-plan / 风险',
  },
  developer: {
    id: 'developer',
    name: 'Developer',
    emoji: '⚙️',
    bubbleClass: 'bg-emerald-50 border-emerald-200',
    ringClass: 'ring-emerald-300 bg-emerald-100 text-emerald-700',
    badgeClass: 'bg-emerald-100 text-emerald-700',
    hint: '按白名单实施代码',
  },
  qa: {
    id: 'qa',
    name: 'QA',
    emoji: '🧪',
    bubbleClass: 'bg-cyan-50 border-cyan-200',
    ringClass: 'ring-cyan-300 bg-cyan-100 text-cyan-700',
    badgeClass: 'bg-cyan-100 text-cyan-700',
    hint: '验收 + 测试报告',
  },
  human: {
    id: 'human',
    name: 'Human',
    emoji: '🧑',
    bubbleClass: 'bg-stone-50 border-stone-200',
    ringClass: 'ring-stone-300 bg-stone-100 text-stone-700',
    badgeClass: 'bg-stone-100 text-stone-700',
    hint: '审批 / 拍板 / 给反馈',
  },
};

export const AGENT_LIST: AgentMeta[] = [
  AGENTS.controller,
  AGENTS.pm,
  AGENTS.architect,
  AGENTS.developer,
  AGENTS.qa,
  AGENTS.human,
];

export function agentMetaOf(id: string | null | undefined): AgentMeta {
  if (!id) return AGENTS.controller;
  if (id in AGENTS) return AGENTS[id as AgentId];
  return AGENTS.controller;
}
