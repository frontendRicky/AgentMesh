import { Check, Loader2, Lock, AlertCircle } from 'lucide-react';

import { cn } from '@/lib/cn';
import { TIMELINE_STAGES, stageStatus } from '@/constants/prompt-keywords';
import type { CurrentStatus } from '@/types/state';

interface TimelineProps {
  current: CurrentStatus;
  isBlocked?: boolean;
  className?: string;
}

const STATE_STYLE = {
  pending: 'bg-stone-100 text-stone-400 border-stone-200',
  running: 'bg-sky-100 text-sky-700 border-sky-300 animate-pulse',
  passed: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  blocked: 'bg-red-100 text-red-700 border-red-300',
};

export function MiniTimeline({ current, isBlocked = false, className }: TimelineProps) {
  return (
    <div className={cn('flex items-center gap-1 overflow-x-auto scrollbar-thin', className)}>
      {TIMELINE_STAGES.map((stage, idx) => {
        const st = stageStatus(stage.statuses, current, isBlocked);
        return (
          <div key={stage.key} className="flex items-center gap-1">
            <div
              className={cn(
                'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium whitespace-nowrap',
                STATE_STYLE[st],
              )}
            >
              <StageIcon state={st} />
              <span>{stage.label}</span>
            </div>
            {idx < TIMELINE_STAGES.length - 1 ? (
              <div
                className={cn(
                  'h-0.5 w-4',
                  st === 'passed' ? 'bg-emerald-300' : 'bg-stone-200',
                )}
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function StageIcon({ state }: { state: 'pending' | 'running' | 'passed' | 'blocked' }) {
  if (state === 'passed') return <Check className="h-3 w-3" />;
  if (state === 'running') return <Loader2 className="h-3 w-3 animate-spin" />;
  if (state === 'blocked') return <AlertCircle className="h-3 w-3" />;
  return <Lock className="h-3 w-3" />;
}
