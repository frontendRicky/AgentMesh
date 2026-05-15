import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { ContextUsageBar } from '@/components/ContextUsageBar';
import { useMetrics } from '@/hooks/useMetrics';
import { formatNumber, formatSize } from '@/lib/format';

export default function Metrics({ taskId }: { taskId: string }) {
  const { data, loading, error } = useMetrics(taskId);

  if (loading) return <div className="p-5 text-sm text-muted-foreground">加载中...</div>;
  if (error) return <div className="p-5"><Empty title="加载失败" description={error.message} /></div>;
  if (!data) return null;

  const byAgent = Object.entries(data.tokens.by_agent).map(([agent, tokens]) => ({ agent, tokens }));
  const byStage = Object.entries(data.tokens.by_stage).map(([stage, tokens]) => ({ stage, tokens }));

  return (
    <div className="space-y-4 px-5 py-5">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">Total tokens</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-semibold tabular-nums">{formatNumber(data.tokens.total_estimate)}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">Active chars</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-semibold tabular-nums">{formatNumber(data.context.active_chars)}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">Context level</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold capitalize">{data.context.level}</p>
            <p className="text-xs text-muted-foreground">{(data.context.usage_pct * 100).toFixed(1)}%</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Context 使用</CardTitle>
          <CardDescription>
            模型 {data.context.model ?? '—'} · 窗口 {formatNumber(data.context.model_max_context)} tokens · chars/3.5 估算
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ContextUsageBar
            tokens={data.context.active_tokens_estimate}
            model={data.context.model}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Largest artifacts</CardTitle>
          <CardDescription>按文件字节数降序，路径相对 task 根目录</CardDescription>
        </CardHeader>
        <CardContent>
          {data.largest_artifacts.length === 0 ? (
            <Empty title="暂无文件" description="当前 task 目录还没有可统计文件" />
          ) : (
            <div className="divide-y rounded border">
              {data.largest_artifacts.map((item) => (
                <div
                  key={item.path}
                  className="grid grid-cols-[minmax(0,1fr)_110px_110px] items-center gap-3 px-3 py-2 text-sm"
                >
                  <span className="truncate font-mono text-xs text-foreground" title={item.path}>
                    {item.path}
                  </span>
                  <span className="text-right tabular-nums text-muted-foreground">
                    {formatSize(item.size_bytes)}
                  </span>
                  <span className="text-right tabular-nums text-muted-foreground">
                    {formatNumber(item.tokens_estimate)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>按 Agent（tokens 估算）</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byAgent}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="agent" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="tokens" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>按 Stage（tokens 估算）</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byStage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="tokens" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
