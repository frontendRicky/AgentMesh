import { Link } from 'react-router-dom';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/StatusBadge';
import { toast } from '@/components/ui/sonner';
import { useTaskList } from '@/hooks/useTaskList';
import { useActiveTask } from '@/hooks/useActiveTask';
import { apiPost, type ApiError } from '@/hooks/useApi';
import { useSettingsStore } from '@/store/settingsStore';
import { formatNumber, formatTime } from '@/lib/format';
import { cn } from '@/lib/cn';

export default function Tasks() {
  const { data, error, loading } = useTaskList();
  const { data: active } = useActiveTask();
  const expertMode = useSettingsStore((s) => s.expertMode);
  const activeId = active?.active_task_id ?? null;

  async function handleRunTask(taskId: string, agent: string | null): Promise<void> {
    try {
      await apiPost('/api/a2a/runs', {
        task_id: taskId,
        agent: agent ?? 'developer',
      });
      toast.success(`已加入执行队列：${taskId}`);
    } catch (e) {
      toast.error(`执行失败：${formatApiError(e)}`);
    }
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin px-6 py-5">
      <Card>
        <CardHeader>
          <CardTitle>{expertMode ? '所有 Task' : '我的任务'}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <Empty title="加载失败" description={`${error.code}: ${error.message}`} />
          ) : !data || data.items.length === 0 ? (
            <Empty
              title={expertMode ? '还没有 task' : '还没有任务'}
              description={
                expertMode
                  ? '跑 `a2a-agent task new <slug>` 创建一个。'
                  : '先去“生成项目”创建一个任务包。'
              }
              action={
                expertMode ? null : (
                  <Link
                    to="/generator"
                    className="text-xs font-medium text-sky-700 hover:underline"
                  >
                    去生成第一个任务包
                  </Link>
                )
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="py-2">{expertMode ? 'Task ID' : '任务编号'}</th>
                    <th>标题</th>
                    <th>状态</th>
                    {expertMode ? <th>当前 Agent</th> : null}
                    {expertMode ? <th className="text-right">Tokens</th> : null}
                    {expertMode ? <th className="text-right">Artifacts</th> : null}
                    <th>更新时间</th>
                    {!expertMode ? <th>操作</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((t) => (
                    <tr
                      key={t.task_id}
                      className={cn(
                        'border-b border-border/60 transition-colors hover:bg-muted/40',
                        t.task_id === activeId && 'bg-amber-50/60 hover:bg-amber-50',
                      )}
                    >
                      <td className="py-2.5">
                        {expertMode ? (
                          <Link
                            to={`/tasks/${t.task_id}`}
                            className="font-mono text-xs text-sky-700 hover:underline"
                          >
                            {t.task_id}
                          </Link>
                        ) : (
                          <Link
                            to={`/tasks/${t.task_id}`}
                            className="font-mono text-xs text-sky-700 hover:underline"
                          >
                            {t.task_id}
                          </Link>
                        )}
                        {t.task_id === activeId ? (
                          <span className="ml-1 rounded bg-amber-100 px-1 py-0.5 text-[10px] text-amber-800">
                            {expertMode ? 'active' : '当前'}
                          </span>
                        ) : null}
                      </td>
                      <td className="max-w-[220px] truncate" title={t.task_title ?? ''}>
                        {t.task_title ?? '—'}
                      </td>
                      <td>
                        <StatusBadge status={t.current_status} />
                      </td>
                      {expertMode ? <td className="text-xs">{t.current_agent ?? '—'}</td> : null}
                      {expertMode ? (
                        <td className="text-right text-xs tabular-nums">
                          {formatNumber(t.token_total_estimate)}
                        </td>
                      ) : null}
                      {expertMode ? (
                        <td className="text-right text-xs tabular-nums">
                          {formatNumber(t.produced_artifacts_count)}
                        </td>
                      ) : null}
                      <td className="text-xs text-muted-foreground">{formatTime(t.updated_at)}</td>
                      {!expertMode ? (
                        <td>
                          <div className="flex items-center gap-2">
                            <Link
                              to={`/tasks/${t.task_id}`}
                              className="text-xs text-sky-700 hover:underline"
                            >
                              查看
                            </Link>
                            <button
                              type="button"
                              className="text-xs text-sky-700 hover:underline"
                              onClick={() => {
                                void handleRunTask(t.task_id, t.current_agent);
                              }}
                            >
                              执行
                            </button>
                            <a
                              href={`/api/a2a/tasks/${t.task_id}/download`}
                              download={`${t.task_id}.zip`}
                              className="text-xs text-sky-700 hover:underline"
                            >
                              下载
                            </a>
                          </div>
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function formatApiError(error: unknown): string {
  if (isApiError(error)) return `${error.code} - ${error.message}`;
  return String(error);
}

function isApiError(error: unknown): error is ApiError {
  if (error === null || typeof error !== 'object') return false;
  return 'code' in error && 'message' in error;
}
