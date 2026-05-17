import { useEffect, useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Empty } from '@/components/ui/empty';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from '@/components/ui/sonner';
import { apiGet, apiPost, type ApiError } from '@/hooks/useApi';

type ProjectType = 'self_upgrade' | 'client_project' | 'generated_project' | 'maintenance';
type AutomationMode = 'manual' | 'assisted' | 'selective_auto' | 'full_auto';

interface Project {
  project_id: string;
  project_name: string;
  project_root: string;
  project_type: ProjectType;
  automation_mode: AutomationMode;
  max_parallel_runs: number;
  allowed_paths: string[];
  blocked_paths: string[];
  created_at: string;
  updated_at: string;
}

const projectTypeOptions: Array<{ value: ProjectType; label: string }> = [
  { value: 'self_upgrade', label: '自升级' },
  { value: 'client_project', label: '客户项目' },
  { value: 'generated_project', label: '生成项目' },
  { value: 'maintenance', label: '维护项目' },
];

export default function Projects() {
  const [items, setItems] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    project_name: '',
    project_root: '',
    project_type: 'client_project' as ProjectType,
  });

  async function refresh(): Promise<void> {
    setLoading(true);
    try {
      setItems(await fetchProjects());
    } catch (e) {
      toast.error(`加载失败：${formatApiError(e)}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!form.project_name.trim() || !form.project_root.trim()) {
      toast.error('请填写项目名称和项目根目录');
      return;
    }

    setSubmitting(true);
    try {
      await apiPost('/api/a2a/projects', {
        project_name: form.project_name.trim(),
        project_root: form.project_root.trim(),
        project_type: form.project_type,
      });
      toast.success('项目已添加');
      setDialogOpen(false);
      setForm({ project_name: '', project_root: '', project_type: 'client_project' });
      await refresh();
    } catch (e) {
      toast.error(`添加失败：${formatApiError(e)}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function remove(projectId: string): Promise<void> {
    try {
      await deleteProject(projectId);
      toast.success('项目已删除');
      await refresh();
    } catch (e) {
      toast.error(`删除失败：${formatApiError(e)}`);
    }
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin px-6 py-5">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <CardTitle>项目</CardTitle>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            添加项目
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <Empty title="还没有项目" description="添加一个 project_root，开始管理多项目并线。" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="py-2">项目名称</th>
                    <th>类型</th>
                    <th>自动化模式</th>
                    <th>项目根目录</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((project) => (
                    <tr key={project.project_id} className="border-b border-border/60">
                      <td className="py-2.5 font-medium">{project.project_name}</td>
                      <td className="text-xs">{projectTypeLabel(project.project_type)}</td>
                      <td className="font-mono text-xs">{project.automation_mode}</td>
                      <td className="max-w-[420px] truncate font-mono text-xs" title={project.project_root}>
                        {project.project_root}
                      </td>
                      <td>
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() => {
                            void remove(project.project_id);
                          }}
                        >
                          删除
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>添加项目</DialogTitle>
            <DialogDescription>
              记录一个 project_root，后续 Run Session 可以绑定到独立项目 lane。
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={(event) => void submit(event)}>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted-foreground">项目名称</span>
              <Input
                value={form.project_name}
                onChange={(event) => setForm((prev) => ({ ...prev, project_name: event.target.value }))}
                placeholder="AgentMesh 自升级"
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted-foreground">项目根目录</span>
              <Input
                value={form.project_root}
                onChange={(event) => setForm((prev) => ({ ...prev, project_root: event.target.value }))}
                placeholder="/Users/you/work/projects/AgentMesh"
              />
            </label>
            <label className="block space-y-1.5 text-sm">
              <span className="text-muted-foreground">项目类型</span>
              <select
                value={form.project_type}
                onChange={(event) => {
                  const next = parseProjectType(event.target.value);
                  if (next) setForm((prev) => ({ ...prev, project_type: next }));
                }}
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
              >
                {projectTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                取消
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? '添加中…' : '添加'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

async function fetchProjects(): Promise<Project[]> {
  const raw = await apiGet<unknown>('/api/a2a/projects');
  if (!Array.isArray(raw)) return [];
  return raw.filter(isProject);
}

async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`/api/a2a/projects/${encodeURIComponent(projectId)}`, {
    method: 'DELETE',
  });
  if (res.status === 204) return;
  let raw: unknown = null;
  try {
    raw = await res.json();
  } catch {
    throw { code: 'PARSE_ERROR', message: `非 JSON 响应 (${res.status})`, status: res.status } as ApiError;
  }
  throw apiErrorFromEnvelope(raw, res.status);
}

function projectTypeLabel(type: ProjectType): string {
  if (type === 'self_upgrade') return '自升级';
  if (type === 'client_project') return '客户项目';
  if (type === 'generated_project') return '生成项目';
  return '维护项目';
}

function formatApiError(error: unknown): string {
  if (isApiError(error)) return `${error.code} - ${error.message}`;
  return String(error);
}

function apiErrorFromEnvelope(raw: unknown, status: number): ApiError {
  if (raw !== null && typeof raw === 'object') {
    const envelope = raw as Record<string, unknown>;
    const error = envelope['error'];
    if (error !== null && typeof error === 'object') {
      const record = error as Record<string, unknown>;
      return {
        code: typeof record['code'] === 'string' ? record['code'] : 'UNKNOWN',
        message: typeof record['message'] === 'string' ? record['message'] : `请求失败 (${status})`,
        status,
      };
    }
  }
  return { code: 'UNKNOWN', message: `请求失败 (${status})`, status };
}

function isApiError(error: unknown): error is ApiError {
  if (error === null || typeof error !== 'object') return false;
  return 'code' in error && 'message' in error;
}

function isProject(value: unknown): value is Project {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record['project_id'] === 'string'
    && typeof record['project_name'] === 'string'
    && typeof record['project_root'] === 'string'
    && parseProjectType(record['project_type']) !== null
    && isAutomationMode(record['automation_mode'])
    && typeof record['max_parallel_runs'] === 'number'
    && Array.isArray(record['allowed_paths'])
    && Array.isArray(record['blocked_paths'])
    && typeof record['created_at'] === 'string'
    && typeof record['updated_at'] === 'string'
  );
}

function parseProjectType(value: unknown): ProjectType | null {
  if (
    value === 'self_upgrade'
    || value === 'client_project'
    || value === 'generated_project'
    || value === 'maintenance'
  ) {
    return value;
  }
  return null;
}

function isAutomationMode(value: unknown): value is AutomationMode {
  return (
    value === 'manual'
    || value === 'assisted'
    || value === 'selective_auto'
    || value === 'full_auto'
  );
}
