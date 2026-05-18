import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { apiGet, apiPost, type ApiError } from '@/hooks/useApi';

interface SandboxTabProps {
  taskId: string;
}

interface SandboxDiff {
  run_id: string;
  changed_files: string[];
  patch: string;
  patch_size_bytes: number;
}

interface SandboxApplyResult {
  run_id: string;
  applied_files: string[];
  backup_manifest_path: string;
  applied_at: string;
}

interface SandboxRollbackResult {
  run_id: string;
  restored_files: string[];
  rolled_back_at: string;
}

interface TestRunResponse {
  run_id: string;
  project_id: string;
  results: TestResult[];
}

interface TestResult {
  suite: 'typecheck' | 'lint' | 'build';
  status: 'pass' | 'fail' | 'timeout';
  exit_code: number;
  duration_ms: number;
  summary_lines: string[];
  log_path: string;
  toolchain: string;
  created_at: string;
}

export default function SandboxTab({ taskId }: SandboxTabProps) {
  const [runId, setRunId] = useState('');
  const [projectId, setProjectId] = useState('');
  const [sourceFiles, setSourceFiles] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [diff, setDiff] = useState<SandboxDiff | null>(null);
  const [tests, setTests] = useState<TestResult[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  const normalizedRunId = runId.trim();
  const normalizedProjectId = projectId.trim();

  async function runAction<T>(label: string, action: () => Promise<T>, onSuccess?: (value: T) => void): Promise<void> {
    setBusy(label);
    setMessage(null);
    try {
      const result = await action();
      onSuccess?.(result);
      setMessage(`${label} 已完成`);
    } catch (e) {
      setMessage(`${label} 失败：${formatApiError(e)}`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin p-5">
      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Sandbox 控制</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground" htmlFor="sandbox-run-id">Run ID</label>
              <Input
                id="sandbox-run-id"
                value={runId}
                placeholder={`R-${taskId}`}
                onChange={(event) => setRunId(event.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground" htmlFor="sandbox-project-id">Project ID</label>
              <Input
                id="sandbox-project-id"
                value={projectId}
                placeholder="self-upgrade"
                onChange={(event) => setProjectId(event.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground" htmlFor="sandbox-source-files">Source files</label>
              <textarea
                id="sandbox-source-files"
                value={sourceFiles}
                placeholder="apps/a2a-console/client/src/pages/Tasks.tsx"
                className="min-h-24 w-full rounded-md border border-border bg-background px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-ring"
                onChange={(event) => setSourceFiles(event.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                size="xs"
                variant="outline"
                disabled={!normalizedRunId || !normalizedProjectId || busy !== null}
                onClick={() => {
                  void runAction(
                    '初始化',
                    () => apiPost('/api/a2a/sandbox/init', {
                      run_id: normalizedRunId,
                      project_id: normalizedProjectId,
                      source_files: parseSourceFiles(sourceFiles),
                    }),
                  );
                }}
              >
                初始化
              </Button>
              <Button
                type="button"
                size="xs"
                variant="outline"
                disabled={!normalizedRunId || busy !== null}
                onClick={() => {
                  void runAction(
                    '查看 diff',
                    () => apiGet<SandboxDiff>(`/api/a2a/sandbox/${normalizedRunId}/diff`),
                    setDiff,
                  );
                }}
              >
                Diff
              </Button>
              <Button
                type="button"
                size="xs"
                variant="outline"
                disabled={!normalizedRunId || busy !== null}
                onClick={() => {
                  const confirmed = window.confirm('应用后会写回主项目，确认继续？');
                  if (!confirmed) return;
                  void runAction(
                    '应用',
                    () => apiPost<SandboxApplyResult>(`/api/a2a/sandbox/${normalizedRunId}/apply`, {}),
                  );
                }}
              >
                应用
              </Button>
              <Button
                type="button"
                size="xs"
                variant="outline"
                disabled={!normalizedRunId || busy !== null}
                onClick={() => {
                  void runAction(
                    '回滚',
                    () => apiPost<SandboxRollbackResult>(`/api/a2a/sandbox/${normalizedRunId}/rollback`, {}),
                  );
                }}
              >
                回滚
              </Button>
              <Button
                type="button"
                size="xs"
                disabled={!normalizedRunId || !normalizedProjectId || busy !== null}
                onClick={() => {
                  void runAction(
                    '运行测试',
                    () => apiPost<TestRunResponse>('/api/a2a/test/run', {
                      run_id: normalizedRunId,
                      project_id: normalizedProjectId,
                      suites: ['typecheck'],
                    }),
                    (value) => setTests(value.results),
                  );
                }}
              >
                运行 typecheck
              </Button>
            </div>
            {message ? <p className="text-xs text-muted-foreground">{message}</p> : null}
            {busy ? <p className="text-xs text-muted-foreground">{busy} 中...</p> : null}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Diff</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {diff ? (
                <>
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>{diff.changed_files.length} files</span>
                    <span>{diff.patch_size_bytes} bytes</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {diff.changed_files.map((file) => (
                      <code key={file} className="rounded bg-muted px-1.5 py-0.5 text-[11px]">
                        {file}
                      </code>
                    ))}
                  </div>
                  <pre className="max-h-[420px] overflow-auto rounded-md bg-muted p-3 text-xs">
                    {diff.patch || '无改动'}
                  </pre>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">尚未加载 diff。</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>测试结果</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {tests.length > 0 ? (
                tests.map((result) => (
                  <div key={`${result.suite}-${result.created_at}`} className="rounded-md border border-border p-3">
                    <div className="flex items-center justify-between gap-2 text-sm">
                      <span className="font-medium">{result.suite}</span>
                      <span className={statusClass(result.status)}>{result.status}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      exit {result.exit_code} · {result.duration_ms}ms · {result.toolchain}
                    </p>
                    <pre className="mt-2 max-h-36 overflow-auto rounded bg-muted p-2 text-xs">
                      {result.summary_lines.join('\n') || '无错误摘要'}
                    </pre>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">尚未运行测试。</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function parseSourceFiles(value: string): string[] {
  return value.split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean);
}

function formatApiError(error: unknown): string {
  if (isApiError(error)) return `${error.code} - ${error.message}`;
  return String(error);
}

function isApiError(error: unknown): error is ApiError {
  return error !== null && typeof error === 'object' && 'code' in error && 'message' in error;
}

function statusClass(status: TestResult['status']): string {
  if (status === 'pass') return 'rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700';
  if (status === 'timeout') return 'rounded bg-orange-100 px-2 py-0.5 text-xs text-orange-700';
  return 'rounded bg-red-100 px-2 py-0.5 text-xs text-red-700';
}
