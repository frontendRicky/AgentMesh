import { cn } from '@/lib/cn';
import { agentMetaOf } from '@/constants/agent-meta';

interface AgentAvatarProps {
  agent: string | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  showName?: boolean;
  selected?: boolean;
  className?: string;
}

const SIZE_MAP = {
  sm: 'h-8 w-8 text-base',
  md: 'h-10 w-10 text-xl',
  lg: 'h-12 w-12 text-2xl',
};

export function AgentAvatar({ agent, size = 'md', showName, selected, className }: AgentAvatarProps) {
  const meta = agentMetaOf(agent);
  return (
    <div className={cn('flex flex-col items-center gap-1', className)}>
      <div
        className={cn(
          'flex items-center justify-center rounded-full ring-2 ring-offset-2 ring-offset-background transition-all',
          SIZE_MAP[size],
          meta.ringClass,
          selected ? 'ring-4' : 'ring-2',
        )}
        title={meta.hint}
      >
        <span aria-hidden>{meta.emoji}</span>
      </div>
      {showName ? (
        <span className="text-[11px] font-medium text-foreground">{meta.name}</span>
      ) : null}
    </div>
  );
}
