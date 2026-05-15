import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/cn';

const STATUS_LABEL: Record<string, { text: string; color: string }> = {
  created: { text: '新建', color: 'bg-stone-100 text-stone-700' },
  pm_processing: { text: 'PM 进行中', color: 'bg-orange-100 text-orange-700' },
  pm_completed: { text: 'PM 完成', color: 'bg-orange-200 text-orange-900' },
  architect_processing: { text: 'Architect 进行中', color: 'bg-sky-100 text-sky-700' },
  architect_completed: { text: 'Architect 完成', color: 'bg-sky-200 text-sky-900' },
  human_review_required: { text: '等你审批', color: 'bg-amber-100 text-amber-800' },
  developer_processing: { text: 'Developer 进行中', color: 'bg-emerald-100 text-emerald-700' },
  developer_completed: { text: 'Developer 完成', color: 'bg-emerald-200 text-emerald-900' },
  qa_processing: { text: 'QA 进行中', color: 'bg-cyan-100 text-cyan-700' },
  qa_completed: { text: 'QA 完成', color: 'bg-cyan-200 text-cyan-900' },
  final_review_required: { text: '等你最终审批', color: 'bg-amber-100 text-amber-800' },
  completed: { text: '已完成', color: 'bg-green-100 text-green-700' },
  blocked: { text: '阻塞', color: 'bg-red-100 text-red-700' },
  cancelled: { text: '已取消', color: 'bg-stone-100 text-stone-500' },
};

interface StatusBadgeProps {
  status: string | null | undefined;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  if (!status) return <Badge variant="outline" className={className}>—</Badge>;
  const meta = STATUS_LABEL[status] ?? { text: status, color: 'bg-muted text-foreground' };
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium',
        meta.color,
        className,
      )}
    >
      {meta.text}
    </span>
  );
}

const MSG_TYPE_LABEL: Record<string, { text: string; color: string }> = {
  handoff: { text: 'handoff', color: 'bg-sky-100 text-sky-700' },
  request: { text: 'request', color: 'bg-blue-100 text-blue-700' },
  response: { text: 'response', color: 'bg-indigo-100 text-indigo-700' },
  review: { text: 'review', color: 'bg-purple-100 text-purple-700' },
  blocker: { text: 'blocker', color: 'bg-red-100 text-red-700' },
  gate_failure: { text: 'gate failure', color: 'bg-red-100 text-red-700' },
  status: { text: 'status', color: 'bg-stone-100 text-stone-700' },
  final: { text: 'final', color: 'bg-amber-100 text-amber-700' },
};

export function MessageTypeBadge({ type, className }: { type: string | null; className?: string }) {
  if (!type) return null;
  const meta = MSG_TYPE_LABEL[type] ?? { text: type, color: 'bg-muted text-foreground' };
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide',
        meta.color,
        className,
      )}
    >
      {meta.text}
    </span>
  );
}
