import type { CurrentStatus } from '@/types/state';

export interface PromptKeywordEntry {
  keyword: string;
  ui_action: 'copy' | 'show_only' | 'link';
  cli_role: 'controller' | 'pm' | 'architect' | 'developer' | 'qa' | null;
  hint?: string;
  badgeText: string;
  badgeClass: string;
}

export const PROMPT_KEYWORDS: Record<CurrentStatus, PromptKeywordEntry> = {
  created: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
    badgeText: '等 Controller 启动',
    badgeClass: 'bg-stone-100 text-stone-700',
  },
  pm_processing: {
    keyword: 'prompt pm',
    ui_action: 'copy',
    cli_role: 'pm',
    badgeText: 'PM 在拆需求',
    badgeClass: 'bg-orange-100 text-orange-700',
  },
  pm_completed: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
    badgeText: 'PM 完成，等推进',
    badgeClass: 'bg-purple-100 text-purple-700',
  },
  architect_processing: {
    keyword: 'prompt architect',
    ui_action: 'copy',
    cli_role: 'architect',
    badgeText: 'Architect 在出方案',
    badgeClass: 'bg-sky-100 text-sky-700',
  },
  architect_completed: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
    badgeText: 'Architect 完成，等推进',
    badgeClass: 'bg-purple-100 text-purple-700',
  },
  human_review_required: {
    keyword: '',
    ui_action: 'show_only',
    cli_role: null,
    hint: '请在 Cursor 代写 architect-review.md，让 Controller 推进',
    badgeText: '等你审批',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
  developer_processing: {
    keyword: 'prompt developer',
    ui_action: 'copy',
    cli_role: 'developer',
    badgeText: 'Developer 在写代码',
    badgeClass: 'bg-emerald-100 text-emerald-700',
  },
  developer_completed: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
    badgeText: 'Developer 完成，等推进',
    badgeClass: 'bg-purple-100 text-purple-700',
  },
  qa_processing: {
    keyword: 'prompt qa',
    ui_action: 'copy',
    cli_role: 'qa',
    badgeText: 'QA 在验收',
    badgeClass: 'bg-cyan-100 text-cyan-700',
  },
  qa_completed: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
    badgeText: 'QA 完成，等推进',
    badgeClass: 'bg-purple-100 text-purple-700',
  },
  final_review_required: {
    keyword: '',
    ui_action: 'show_only',
    cli_role: null,
    hint: '请在 Cursor 代写 final-review.md，让 Controller 推进',
    badgeText: '等你最终审批',
    badgeClass: 'bg-amber-100 text-amber-700',
  },
  completed: {
    keyword: '',
    ui_action: 'link',
    cli_role: null,
    hint: '查看 final-delivery.md',
    badgeText: '已完成',
    badgeClass: 'bg-green-100 text-green-700',
  },
  blocked: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
    badgeText: 'Blocker 阻塞中',
    badgeClass: 'bg-red-100 text-red-700',
  },
  cancelled: {
    keyword: '',
    ui_action: 'show_only',
    cli_role: null,
    hint: 'Task 已取消',
    badgeText: '已取消',
    badgeClass: 'bg-stone-100 text-stone-700',
  },
};

export const TIMELINE_STAGES: { key: string; label: string; statuses: CurrentStatus[] }[] = [
  { key: 'pm', label: 'PM', statuses: ['pm_processing', 'pm_completed'] },
  {
    key: 'architect',
    label: 'Architect',
    statuses: ['architect_processing', 'architect_completed'],
  },
  { key: 'human_review', label: 'Human Review', statuses: ['human_review_required'] },
  {
    key: 'developer',
    label: 'Developer',
    statuses: ['developer_processing', 'developer_completed'],
  },
  { key: 'qa', label: 'QA', statuses: ['qa_processing', 'qa_completed'] },
  { key: 'final_review', label: 'Final Review', statuses: ['final_review_required'] },
  { key: 'completed', label: 'Done', statuses: ['completed'] },
];

const STATUS_ORDER: CurrentStatus[] = [
  'created',
  'pm_processing',
  'pm_completed',
  'architect_processing',
  'architect_completed',
  'human_review_required',
  'developer_processing',
  'developer_completed',
  'qa_processing',
  'qa_completed',
  'final_review_required',
  'completed',
];

export function stageStatus(
  stageStatuses: CurrentStatus[],
  current: CurrentStatus,
  isBlocked: boolean,
): 'pending' | 'running' | 'passed' | 'blocked' {
  if (stageStatuses.includes(current)) {
    return isBlocked ? 'blocked' : 'running';
  }
  const currentIdx = STATUS_ORDER.indexOf(current);
  const stageMaxIdx = Math.max(...stageStatuses.map((s) => STATUS_ORDER.indexOf(s)));
  if (currentIdx > stageMaxIdx && currentIdx >= 0) return 'passed';
  return 'pending';
}
