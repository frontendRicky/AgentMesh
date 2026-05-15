import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from '@/components/ui/sonner';
import { apiPost } from '@/hooks/useApi';
import { useProjectRoot } from '@/hooks/useActiveTask';
import { useSettingsStore } from '@/store/settingsStore';
import { formatTime } from '@/lib/format';

export default function Settings() {
  const { data, refresh } = useProjectRoot();
  const [path, setPath] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const pollIntervalMs = useSettingsStore((s) => s.pollIntervalMs);
  const setPollInterval = useSettingsStore((s) => s.setPollInterval);
  const expertMode = useSettingsStore((s) => s.expertMode);
  const setExpertMode = useSettingsStore((s) => s.setExpertMode);

  useEffect(() => {
    if (data?.project_root) setPath(data.project_root);
  }, [data?.project_root]);

  async function submit() {
    if (!path.trim()) {
      toast.error('请输入项目根路径');
      return;
    }
    setSubmitting(true);
    try {
      await apiPost('/api/a2a/config/project-root', { project_root: path.trim() });
      toast.success('已更新项目根目录');
      refresh();
    } catch (e) {
      const err = e as { code?: string; message?: string };
      toast.error(`更新失败：${err.code ?? 'ERR'} - ${err.message ?? ''}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4 p-6">
      <Card>
        <CardHeader>
          <CardTitle>A2A 项目根目录</CardTitle>
          <CardDescription>
            指向包含 <code>.ai-agents/workspace/</code> 的目录。普通模式只会在这里创建新的任务包。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/Users/you/work/projects/AgentMesh"
            />
            <Button onClick={submit} disabled={submitting}>
              {submitting ? '保存中…' : '保存'}
            </Button>
          </div>
          {data?.project_root ? (
            <p className="text-xs text-muted-foreground">
              当前：<code>{data.project_root}</code> · 配置时间 {formatTime(data.configured_at)}
            </p>
          ) : (
            <Alert variant="warning">
              <AlertTitle>未配置项目根</AlertTitle>
              <AlertDescription>
                配置后才能看到 task 列表 / 群聊 / artifacts。
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>显示模式</CardTitle>
          <CardDescription>
            普通模式给非技术同事使用；专家模式保留原有 A2A 工作台。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant={expertMode ? 'outline' : 'secondary'} onClick={() => setExpertMode(!expertMode)}>
            {expertMode ? '切到普通模式' : '切到专家模式'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>轮询间隔</CardTitle>
          <CardDescription>每隔 N ms 重新拉取数据。最小 1000。</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              value={pollIntervalMs}
              onChange={(e) => setPollInterval(Number(e.target.value) || 5000)}
              className="w-32"
            />
            <span className="text-xs text-muted-foreground">毫秒</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>关于</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-xs text-muted-foreground">
          <p>A2A Console MVP · Vite + React + Express</p>
          <p>普通模式只写新的任务包，不启动执行流程，不调用模型。</p>
          <p>本地开发：client 5173 / server 5174。</p>
        </CardContent>
      </Card>
    </div>
  );
}
