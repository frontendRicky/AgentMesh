import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { modelMaxContext } from '@/constants/model-context';
import { formatNumber } from '@/lib/format';
import { cn } from '@/lib/cn';

interface ContextUsageBarProps {
  tokens: number;
  model?: string | null;
  className?: string;
}

export function ContextUsageBar({ tokens, model, className }: ContextUsageBarProps) {
  const max = modelMaxContext(model);
  const ratio = Math.min(1, tokens / max);
  const pct = Math.round(ratio * 100);
  const color =
    ratio >= 0.85 ? 'bg-red-500' : ratio >= 0.6 ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn('w-full', className)}>
            <div className="mb-1 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Context</span>
              <span>
                {formatNumber(tokens)} / {formatNumber(max)} ({pct}%)
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={cn('h-full rounded-full transition-all', color)}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-xs">
            <p>Token 估算：chars / 3.5（粗略）</p>
            <p>当前模型：{model ?? '未配置'}</p>
            <p>窗口上限：{formatNumber(max)} tokens</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
