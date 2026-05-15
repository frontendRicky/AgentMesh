import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/StatusBadge';
import { agentMetaOf } from '@/constants/agent-meta';
import { formatTime } from '@/lib/format';
import type { TaskDetailData } from '@/hooks/useTaskDetail';

export default function Overview({ detail }: { detail: TaskDetailData }) {
  const { task, state } = detail;
  return (
    <div className="grid gap-4 px-5 py-5 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Task 元信息</CardTitle>
          <CardDescription>来自 task.md（不可变）</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Row label="ID">{task.task_id}</Row>
          <Row label="标题">{task.task_title}</Row>
          <Row label="类型">
            <Badge variant="secondary">{task.task_type}</Badge>
          </Row>
          <Row label="优先级">{task.priority}</Row>
          <Row label="负责人">{task.human_owner}</Row>
          <Row label="创建时间">{formatTime(task.created_at)}</Row>
          <Row label="In scope">
            <ul className="list-disc pl-5 text-xs">
              {(task.scope?.in_scope ?? []).map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </Row>
          <Row label="Out of scope">
            <ul className="list-disc pl-5 text-xs text-muted-foreground">
              {(task.scope?.out_of_scope ?? []).map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </Row>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>State（动态）</CardTitle>
          <CardDescription>来自 state.md，由 Controller 维护</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Row label="状态"><StatusBadge status={state.current_status} /></Row>
          <Row label="上一状态"><code className="text-xs">{state.previous_status}</code></Row>
          <Row label="当前 Agent">{agentMetaOf(state.current_agent).emoji} {agentMetaOf(state.current_agent).name}</Row>
          <Row label="下一棒">{agentMetaOf(state.next_agent).emoji} {agentMetaOf(state.next_agent).name}</Row>
          <Row label="允许的下一状态">
            <div className="flex flex-wrap gap-1">
              {(state.allowed_next_statuses ?? []).map((s) => (
                <Badge key={s} variant="outline" className="text-[10px]">{s}</Badge>
              ))}
            </div>
          </Row>
          <Row label="Human Review"><code className="text-xs">{state.human_review_status}</code></Row>
          <Row label="Final Review"><code className="text-xs">{state.final_review_status}</code></Row>
          <Row label="已产出 artifacts">{state.produced_artifacts?.length ?? 0}</Row>
          <Row label="active blocker">{state.active_blocker ?? '—'}</Row>
          <Row label="更新时间">{formatTime(state.updated_at)}</Row>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[110px_1fr] items-start gap-3">
      <span className="pt-0.5 text-xs text-muted-foreground">{label}</span>
      <div>{children}</div>
    </div>
  );
}
