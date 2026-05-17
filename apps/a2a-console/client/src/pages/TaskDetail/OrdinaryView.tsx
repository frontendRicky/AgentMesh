import { Link } from 'react-router-dom';
import { Download } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/StatusBadge';
import { agentMetaOf } from '@/constants/agent-meta';
import type { TaskDetailData } from '@/hooks/useTaskDetail';

interface OrdinaryViewProps {
  taskId: string;
  data: TaskDetailData;
}

export default function OrdinaryView({ taskId, data }: OrdinaryViewProps) {
  const state = data.state as Record<string, unknown>;
  const task = data.task as Record<string, unknown>;
  const status = (state['current_status'] as string | null) ?? null;
  const currentAgent = (state['current_agent'] as string | null) ?? null;
  const taskTitle = (task['task_title'] as string | null) ?? taskId;
  const agentName = agentMetaOf(currentAgent).name;

  return (
    <div className="h-full overflow-y-auto scrollbar-thin px-5 py-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{taskTitle}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground w-20 shrink-0">当前状态</span>
            <StatusBadge status={status} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground w-20 shrink-0">当前阶段</span>
            <span>{agentName}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground w-20 shrink-0">任务编号</span>
            <code className="font-mono text-xs">{taskId}</code>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">下载任务包</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            把整个任务包打包下载，交给技术同事在 Cursor / Codex 中继续。
          </p>
          <Button asChild size="sm" variant="outline">
            <a href={`/api/a2a/tasks/${taskId}/download`} download={`${taskId}.zip`}>
              <Download className="mr-1.5 h-4 w-4" />
              下载任务包 (.zip)
            </a>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">如何继续</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-1">
          <p>1. 点击上方「下载任务包」，把 .zip 发给技术同事。</p>
          <p>2. 技术同事解压后，在 Cursor 中打开项目根目录。</p>
          <p>3. 按 task.md 里的说明继续使用 a2a-agent 推进流程。</p>
        </CardContent>
      </Card>

      <div className="pt-1">
        <Button asChild size="sm" variant="ghost">
          <Link to="/tasks">← 返回任务列表</Link>
        </Button>
      </div>
    </div>
  );
}
