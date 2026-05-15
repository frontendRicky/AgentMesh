import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { AgentAvatar } from '@/components/AgentAvatar';
import { MessageTypeBadge } from '@/components/StatusBadge';
import { useMessages } from '@/hooks/useMessages';
import { agentMetaOf } from '@/constants/agent-meta';
import { formatRelative, formatTime } from '@/lib/format';

export default function Timeline({ taskId }: { taskId: string }) {
  const { data, loading } = useMessages(taskId);
  const items = data?.items ?? [];

  return (
    <div className="px-5 py-5">
      <Card>
        <CardHeader>
          <CardTitle>时间线（按 created_at 升序）</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">加载中...</p>
          ) : items.length === 0 ? (
            <Empty title="还没有事件" />
          ) : (
            <ol className="relative space-y-3 border-l border-border pl-6">
              {items.map((m) => (
                <li key={m.message_id ?? m.file_path} className="relative">
                  <span className="absolute -left-[34px] top-0">
                    <AgentAvatar agent={m.from_agent} size="sm" />
                  </span>
                  <div className="rounded-md border border-border bg-card px-3 py-2 shadow-sm">
                    <div className="mb-1 flex flex-wrap items-baseline gap-2">
                      <span className="text-xs font-semibold">{agentMetaOf(m.from_agent).name}</span>
                      <MessageTypeBadge type={m.message_type ?? null} />
                      {m.to_agent ? (
                        <span className="text-[10px] text-muted-foreground">→ {agentMetaOf(m.to_agent).name}</span>
                      ) : null}
                      <span className="text-[10px] text-muted-foreground" title={formatTime(m.created_at)}>
                        {formatRelative(m.created_at)}
                      </span>
                    </div>
                    {m.intent ? <p className="text-[11px] font-medium uppercase tracking-wide text-foreground/60">{m.intent}</p> : null}
                    <p className="mt-1 text-sm text-foreground/90">{m.summary ?? '—'}</p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
