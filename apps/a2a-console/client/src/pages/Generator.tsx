import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ClipboardList, FileText, Loader2, WandSparkles } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  DEFAULT_PAGES,
  GENERATION_STRATEGY_OPTIONS,
  MODEL_PROFILE_OPTIONS,
  PROJECT_TYPE_LABELS,
} from '@/constants/generator';
import {
  createProjectGeneratorDraft,
  createProjectGeneratorTask,
  getProjectGeneratorTemplates,
} from '@/hooks/useProjectGenerator';
import { toast } from '@/components/ui/sonner';
import { useSettingsStore } from '@/store/settingsStore';
import type {
  ProjectGeneratorDraftRequest,
  ProjectGeneratorDraftResponse,
  ProjectGeneratorProjectType,
  ProjectGeneratorTaskCreateResponse,
  ProjectGeneratorTemplate,
} from '@a2a-console/contract';

const SLUG_RE = /^[a-z0-9-]{1,40}$/;

export default function Generator() {
  const lastSelection = useSettingsStore((s) => s.generatorLastSelection);
  const setLastSelection = useSettingsStore((s) => s.setGeneratorLastSelection);
  const [templates, setTemplates] = useState<ProjectGeneratorTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  const [draft, setDraft] = useState<ProjectGeneratorDraftResponse | null>(null);
  const [createdTask, setCreatedTask] = useState<ProjectGeneratorTaskCreateResponse | null>(null);
  const [submittingDraft, setSubmittingDraft] = useState(false);
  const [creatingTask, setCreatingTask] = useState(false);
  const [pagesText, setPagesText] = useState(DEFAULT_PAGES.join('\n'));
  const [slug, setSlug] = useState('');
  const [form, setForm] = useState<ProjectGeneratorDraftRequest>({
    project_name: '',
    project_type: (lastSelection.projectType || 'business-dashboard') as ProjectGeneratorProjectType,
    business_description: '',
    target_users: '',
    pages: DEFAULT_PAGES,
    style_preference: '',
    data_source: '',
    generation_strategy: (lastSelection.generationStrategy || 'quality') as ProjectGeneratorDraftRequest['generation_strategy'],
    model_profile: (lastSelection.modelProfile || 'recommended') as ProjectGeneratorDraftRequest['model_profile'],
    api_mode: 'mock',
    needs_auth: false,
    needs_charts: false,
  });

  useEffect(() => {
    let cancelled = false;
    getProjectGeneratorTemplates()
      .then((data) => {
        if (cancelled) return;
        setTemplates(data.items);
        setTemplatesError(null);
      })
      .catch((e: { code?: string; message?: string }) => {
        if (cancelled) return;
        setTemplatesError(`${e.code ?? 'ERR'}: ${e.message ?? '加载失败'}`);
      })
      .finally(() => {
        if (!cancelled) setTemplatesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const pages = useMemo(
    () =>
      pagesText
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean),
    [pagesText],
  );

  const canPreview =
    form.project_name.trim().length > 0 &&
    form.business_description.trim().length >= 10 &&
    !submittingDraft;
  const canCreateTask = draft !== null && SLUG_RE.test(slug) && !creatingTask;

  function updateForm<K extends keyof ProjectGeneratorDraftRequest>(
    key: K,
    value: ProjectGeneratorDraftRequest[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
    setDraft(null);
    setCreatedTask(null);
  }

  async function submitDraft() {
    if (!canPreview) {
      toast.error('请先填写项目名称，并用一句话以上说明业务需求。');
      return;
    }
    setSubmittingDraft(true);
    try {
      const payload: ProjectGeneratorDraftRequest = {
        ...form,
        project_name: form.project_name.trim(),
        business_description: form.business_description.trim(),
        target_users: form.target_users.trim(),
        style_preference: form.style_preference.trim(),
        data_source: form.data_source.trim(),
        pages,
      };
      const nextDraft = await createProjectGeneratorDraft(payload);
      setDraft(nextDraft);
      setSlug((current) => current || slugify(payload.project_name));
      setLastSelection({
        projectType: payload.project_type,
        generationStrategy: payload.generation_strategy,
        modelProfile: payload.model_profile,
      });
      toast.success('已整理预览');
    } catch (e) {
      const err = e as { code?: string; message?: string };
      toast.error(`整理失败：${err.code ?? 'ERR'} - ${err.message ?? ''}`);
    } finally {
      setSubmittingDraft(false);
    }
  }

  async function createTask() {
    if (!draft) return;
    if (!SLUG_RE.test(slug)) {
      toast.error('任务短名只能用小写字母、数字和中横线，最多 40 个字符。');
      return;
    }
    setCreatingTask(true);
    try {
      const result = await createProjectGeneratorTask(draft.draft_id, slug);
      setCreatedTask(result);
      toast.success('任务包已创建');
    } catch (e) {
      const err = e as { code?: string; message?: string };
      toast.error(`创建失败：${err.code ?? 'ERR'} - ${err.message ?? ''}`);
    } finally {
      setCreatingTask(false);
    }
  }

  return (
    <TooltipProvider>
      <div className="h-full overflow-y-auto scrollbar-thin">
        <div className="mx-auto flex max-w-6xl flex-col gap-5 px-6 py-5">
          <section className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <WandSparkles className="h-4 w-4 text-sky-700" />
              <span>普通模式</span>
            </div>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-semibold tracking-tight">生成前端项目任务包</h2>
                <p className="max-w-2xl text-sm text-muted-foreground">
                  用中文把想做的页面说清楚，系统会整理成技术同事可以继续执行的任务包。
                </p>
              </div>
              <DisabledNextStep />
            </div>
          </section>

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
            <div className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle>1. 选择项目类型</CardTitle>
                  <CardDescription>选最接近的一类即可，后面还可以用文字补充。</CardDescription>
                </CardHeader>
                <CardContent>
                  {templatesLoading ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {[0, 1, 2, 3].map((item) => (
                        <Skeleton key={item} className="h-24" />
                      ))}
                    </div>
                  ) : templatesError ? (
                    <Empty title="项目类型加载失败" description={templatesError} />
                  ) : (
                    <div className="grid gap-3 md:grid-cols-2">
                      {templates.map((template) => (
                        <button
                          key={template.id}
                          type="button"
                          onClick={() => updateForm('project_type', template.id)}
                          className={[
                            'rounded-lg border p-4 text-left transition-colors',
                            form.project_type === template.id
                              ? 'border-sky-500 bg-sky-50 text-sky-950'
                              : 'border-border bg-background hover:bg-muted',
                          ].join(' ')}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-medium">{PROJECT_TYPE_LABELS[template.id]}</span>
                            {form.project_type === template.id ? (
                              <CheckCircle2 className="h-4 w-4 text-sky-700" />
                            ) : null}
                          </div>
                          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                            {template.description}
                          </p>
                          <p className="mt-2 text-xs text-sky-700">{template.examples.join(' / ')}</p>
                        </button>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>2. 描述你想做什么</CardTitle>
                  <CardDescription>不用写技术词，像给同事交代工作一样描述即可。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <LabeledField label="项目名称">
                    <Input
                      value={form.project_name}
                      onChange={(e) => updateForm('project_name', e.target.value)}
                      placeholder="例如：门店销售看板"
                    />
                  </LabeledField>
                  <LabeledField label="给谁用">
                    <Input
                      value={form.target_users}
                      onChange={(e) => updateForm('target_users', e.target.value)}
                      placeholder="例如：店长、运营同事、老板"
                    />
                  </LabeledField>
                  <LabeledField label="业务说明">
                    <textarea
                      value={form.business_description}
                      onChange={(e) => updateForm('business_description', e.target.value)}
                      rows={6}
                      className="min-h-32 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      placeholder="例如：我想看到每个门店每天卖了多少钱、哪些商品卖得好、库存快不够时要提醒，还要能按日期筛选。"
                    />
                  </LabeledField>
                  <LabeledField label="希望包含哪些页面">
                    <textarea
                      value={pagesText}
                      onChange={(e) => {
                        setPagesText(e.target.value);
                        setDraft(null);
                        setCreatedTask(null);
                      }}
                      rows={4}
                      className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      placeholder={'每行写一个页面，例如：\n首页\n列表页\n详情页'}
                    />
                  </LabeledField>
                  <LabeledField label="喜欢的风格">
                    <Input
                      value={form.style_preference}
                      onChange={(e) => updateForm('style_preference', e.target.value)}
                      placeholder="例如：清爽、适合办公室、重点数字醒目"
                    />
                  </LabeledField>
                  <LabeledField label="数据从哪里来">
                    <Input
                      value={form.data_source}
                      onChange={(e) => updateForm('data_source', e.target.value)}
                      placeholder="例如：先用示例数据，后面再接公司接口"
                    />
                  </LabeledField>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <ToggleOption
                      active={form.api_mode === 'mock'}
                      label="先用示例数据"
                      onClick={() => updateForm('api_mode', 'mock')}
                    />
                    <ToggleOption
                      active={form.needs_auth}
                      label="需要登录"
                      onClick={() => updateForm('needs_auth', !form.needs_auth)}
                    />
                    <ToggleOption
                      active={form.needs_charts}
                      label="需要图表"
                      onClick={() => updateForm('needs_charts', !form.needs_charts)}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>3. 选择生成偏好</CardTitle>
                  <CardDescription>这里不会直接调用模型，只会写入任务包给技术同事参考。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    {GENERATION_STRATEGY_OPTIONS.map((option) => (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => updateForm('generation_strategy', option.id)}
                        className={[
                          'rounded-lg border p-3 text-left transition-colors',
                          form.generation_strategy === option.id
                            ? 'border-emerald-500 bg-emerald-50 text-emerald-950'
                            : 'border-border bg-background hover:bg-muted',
                        ].join(' ')}
                      >
                        <p className="font-medium">{option.label}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{option.hint}</p>
                      </button>
                    ))}
                  </div>
                  <div className="grid gap-3 md:grid-cols-5">
                    {MODEL_PROFILE_OPTIONS.map((option) => (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => updateForm('model_profile', option.id)}
                        className={[
                          'rounded-lg border p-3 text-left transition-colors',
                          form.model_profile === option.id
                            ? 'border-violet-500 bg-violet-50 text-violet-950'
                            : 'border-border bg-background hover:bg-muted',
                        ].join(' ')}
                      >
                        <p className="font-medium">{option.label}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{option.hint}</p>
                        <Badge variant="secondary" className="mt-2">
                          {option.cost}
                        </Badge>
                      </button>
                    ))}
                  </div>
                  <Alert variant="info">
                    <ClipboardList className="h-4 w-4" />
                    <AlertTitle>模型选择只是快照</AlertTitle>
                    <AlertDescription>
                      页面只保存上次选择方便回填，真正执行时以任务包里的“模型选择快照”文件为准。
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>

              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={submitDraft} disabled={!canPreview}>
                  {submittingDraft ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  整理预览
                </Button>
                <p className="text-xs text-muted-foreground">
                  预览不会写文件；点击创建任务包后才会写入工作区。
                </p>
              </div>
            </div>

            <aside className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle>预览</CardTitle>
                  <CardDescription>确认内容没问题后再创建任务包。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!draft ? (
                    <Empty title="还没有预览" description="填写左侧内容后点击“整理预览”。" />
                  ) : (
                    <>
                      <PreviewBlock title="摘要" content={draft.summary} />
                      <PreviewBlock title="产品说明" content={draft.prd_preview} />
                      <PreviewBlock title="技术同事继续说明" content={draft.openspec_preview} />
                      <PreviewBlock title="模型选择快照" content={draft.model_snapshot_preview} />
                      <LabeledField label="任务短名">
                        <Input
                          value={slug}
                          onChange={(e) => setSlug(e.target.value.trim())}
                          placeholder="store-sales-dashboard"
                        />
                        <p className="mt-1 text-xs text-muted-foreground">
                          只允许小写字母、数字、中横线，最多 40 个字符。任务编号由系统自动分配。
                        </p>
                      </LabeledField>
                      <Button onClick={createTask} disabled={!canCreateTask} className="w-full">
                        {creatingTask ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                        创建任务包
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>

              {createdTask ? (
                <Alert variant="info">
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertTitle>任务包已创建</AlertTitle>
                  <AlertDescription>
                    <p>
                      任务编号：<code>{createdTask.task_id}</code>
                    </p>
                    <p>
                      位置：<code>{createdTask.task_path}</code>
                    </p>
                    <p>请把这个任务包交给技术同事，在 Cursor / Codex 中继续。</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button asChild size="sm" variant="outline">
                        <a
                          href={`/api/a2a/tasks/${createdTask.task_id}/download`}
                          download={`${createdTask.task_id}.zip`}
                        >
                          下载任务包 (.zip)
                        </a>
                      </Button>
                      <Button asChild size="sm" variant="ghost">
                        <Link to={`/tasks/${createdTask.task_id}`}>查看任务详情</Link>
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              ) : null}
            </aside>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

function LabeledField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

function ToggleOption({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'rounded-lg border px-3 py-2 text-left text-sm transition-colors',
        active ? 'border-sky-500 bg-sky-50 text-sky-950' : 'border-border bg-background hover:bg-muted',
      ].join(' ')}
    >
      {label}
    </button>
  );
}

function PreviewBlock({ title, content }: { title: string; content: string }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-medium">{title}</h3>
      <pre className="max-h-52 overflow-auto rounded-md border border-border bg-muted/40 p-3 whitespace-pre-wrap break-words text-xs leading-relaxed">
        {content}
      </pre>
    </section>
  );
}

function DisabledNextStep() {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex">
          <Button disabled variant="secondary">
            下一步
          </Button>
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs leading-relaxed">
        本期未开放，请把任务包交给技术同事在 Cursor / Codex 跑。见
        <a className="ml-1 underline" href="/README.md#如何继续">
          README「如何继续」
        </a>
        。
      </TooltipContent>
    </Tooltip>
  );
}

function slugify(value: string): string {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40);
  return normalized || 'frontend-project';
}
