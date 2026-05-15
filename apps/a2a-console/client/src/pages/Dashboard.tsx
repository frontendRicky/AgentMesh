import { Link } from 'react-router-dom';
import { ArrowRight, MessagesSquare } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { Button } from '@/components/ui/button';
import { MessageCard } from '@/components/MessageCard';
import { MiniTimeline } from '@/components/TimelineNode';
import { StatusBadge } from '@/components/StatusBadge';
import { PromptKeywordCard } from '@/components/PromptKeywordCard';
import { ContextUsageBar } from '@/components/ContextUsageBar';
import { Skeleton } from '@/components/ui/skeleton';
import { useActiveTask } from '@/hooks/useActiveTask';
import { useTaskDetail } from '@/hooks/useTaskDetail';
import { useMessages } from '@/hooks/useMessages';
import { useMetrics } from '@/hooks/useMetrics';
import { useBlockers } from '@/hooks/useBlockers';
import { useSettingsStore } from '@/store/settingsStore';
import { useModelStore } from '@/store/modelStore';
import { agentMetaOf } from '@/constants/agent-meta';
import { BlockerCard } from '@/components/BlockerCard';
import type { CurrentStatus } from '@/types/state';

export default function Dashboard() {
  const { data: active, error: activeError } = useActiveTask();
  const taskId = active?.active_task_id ?? null;
  const { data: detail } = useTaskDetail(taskId);
  const { data: msgs, loading: msgsLoading } = useMessages(taskId);
  const { data: metrics } = useMetrics(taskId);
  const { data: blockers } = useBlockers(taskId);
  const agentFilter = useSettingsStore((s) => s.agentFilter);
  const modelSelections = useModelStore((s) => s.selections);

  if (activeError) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Empty
          title="无法读取 active task"
          description={`${activeError.code}: ${activeError.message}。请到「设置」配置 A2A 项目根目录。`}
          action={
            <Button asChild size="sm">
              <Link to="/settings">去设置</Link>
            </Button>
          }
        />
      </div>
    );
  }
  if (!taskId) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Empty
          title="还没有 active task"
          description="可以用 `a2a-agent task use <task_id>` 选一个；或者去 Tasks 列表挑一个 task 查看。"
          action={
            <Button asChild size="sm">
              <Link to="/tasks">查看 Tasks 列表</Link>
            </Button>
          }
        />
      </div>
    );
  }

  const status = (detail?.state.current_status as CurrentStatus) ?? 'created';
  const isBlocked = (blockers?.items?.length ?? 0) > 0;
  const filtered = (msgs?.items ?? []).filter((m) =>
    agentFilter ? m.from_agent === agentFilter : true,
  );
  const currentAgent = detail?.state.current_agent ?? 'controller';
  const currentModel = modelSelections[currentAgent as keyof typeof modelSelections];

  return (
    <div className="grid h-full grid-cols-[1fr_320px] overflow-hidden">
      <section className="flex h-full flex-col overflow-hidden border-r border-border bg-background">
        <header className="border-b border-border px-5 py-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="truncate text-base font-semibold">
                  {detail?.task.task_title ?? taskId}
                </h2>
                <StatusBadge status={status} />
              </div>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                {taskId} · 当前角色：{agentMetaOf(currentAgent).name} · {detail?.state.updated_at ?? '—'}
              </p>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link to={`/tasks/${taskId}`}>
                打开详情 <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
          <div className="mt-3">
            <MiniTimeline current={status} isBlocked={isBlocked} />
          </div>
        </header>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="mx-auto max-w-3xl space-y-4 px-5 py-5">
            {agentFilter ? (
              <div className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
                只显示 <strong>{agentMetaOf(agentFilter).name}</strong> 的消息（点左侧头像取消过滤）
              </div>
            ) : null}

            {msgsLoading ? (
              <ChatSkeleton />
            ) : filtered.length === 0 ? (
              <Empty
                icon={<MessagesSquare className="h-10 w-10" />}
                title="暂无消息"
                description="等 Agent 开干。每条 handoff / blocker / status 都会以气泡显示在这里。"
              />
            ) : (
              filtered.map((m) => <MessageCard key={m.message_id ?? m.file_path} message={m} taskId={taskId} />)
            )}
          </div>
        </div>
      </section>

      <aside className="flex h-full flex-col overflow-y-auto scrollbar-thin bg-muted/30 px-4 py-4 space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">
              当前阶段
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5 text-sm">
            <p>
              <span className="text-muted-foreground">状态：</span>
              <StatusBadge status={status} />
            </p>
            <p>
              <span className="text-muted-foreground">当前角色：</span>
              {agentMetaOf(currentAgent).emoji} {agentMetaOf(currentAgent).name}
            </p>
            <p>
              <span className="text-muted-foreground">下一棒：</span>
              {agentMetaOf(detail?.state.next_agent ?? null).emoji} {agentMetaOf(detail?.state.next_agent ?? null).name}
            </p>
            <p>
              <span className="text-muted-foreground">Human Review：</span>
              <code className="text-[11px]">{detail?.state.human_review_status ?? '—'}</code>
            </p>
          </CardContent>
        </Card>

        <PromptKeywordCard status={status} />

        {metrics ? (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">
                Context 估算
              </CardTitle>
              <CardDescription className="text-[10px]">
                基于 artifacts + messages 总字符数
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <ContextUsageBar
                tokens={metrics.context.active_tokens_estimate}
                model={currentModel ?? metrics.context.model}
              />
              <p className="text-[10px] text-muted-foreground">
                level: {metrics.context.level} · usage {(metrics.context.usage_pct * 100).toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        ) : null}

        {isBlocked && blockers ? (
          <div className="space-y-2">
            {blockers.items.slice(0, 2).map((b) => (
              <BlockerCard key={b.blocker_id ?? b.file_path} blocker={b} />
            ))}
          </div>
        ) : null}
      </aside>
    </div>
  );
}

function ChatSkeleton() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <Skeleton className="h-8 w-8 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-16 w-full rounded-2xl" />
          </div>
        </div>
      ))}
    </div>
  );
}
