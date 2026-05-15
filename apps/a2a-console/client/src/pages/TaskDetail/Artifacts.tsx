import { useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Empty } from '@/components/ui/empty';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ArtifactTree } from '@/components/ArtifactTree';
import { MarkdownPreview } from '@/components/MarkdownPreview';
import { Skeleton } from '@/components/ui/skeleton';
import { useArtifactsTree, useArtifactFile } from '@/hooks/useArtifact';
import { formatSize } from '@/lib/format';
import type { TreeNode } from '@/types/artifact';

function countFiles(nodes: TreeNode[]): number {
  let n = 0;
  for (const node of nodes) {
    if (node.type === 'file') n++;
    else n += countFiles(node.children);
  }
  return n;
}

export default function Artifacts({ taskId }: { taskId: string }) {
  const { data: tree, loading: treeLoading } = useArtifactsTree(taskId);
  const [selected, setSelected] = useState<string | null>(null);
  const { data: file, loading: fileLoading, error: fileError } = useArtifactFile(taskId, selected);

  return (
    <div className="grid h-full grid-cols-[300px_1fr] overflow-hidden">
      <aside className="overflow-y-auto scrollbar-thin border-r border-border bg-background p-3">
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground">
              Artifacts {tree ? `(${countFiles(tree.tree)} 个)` : ''}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {treeLoading ? (
              <Skeleton className="h-32 w-full" />
            ) : !tree || tree.tree.length === 0 ? (
              <Empty title="暂无 artifacts" />
            ) : (
              <ArtifactTree nodes={tree.tree} selectedPath={selected} onSelect={setSelected} />
            )}
          </CardContent>
        </Card>
      </aside>
      <section className="overflow-y-auto scrollbar-thin px-5 py-5">
        {!selected ? (
          <Empty title="选一个文件查看" description="左侧点击 *.md，右侧会渲染。" />
        ) : fileLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : fileError ? (
          <Alert variant="destructive">
            <AlertTitle>读取失败 ({fileError.code})</AlertTitle>
            <AlertDescription>{fileError.message}</AlertDescription>
          </Alert>
        ) : file ? (
          <Card>
            <CardHeader>
              <CardTitle className="font-mono text-sm">{file.path}</CardTitle>
              <p className="text-[11px] text-muted-foreground">
                {formatSize(file.size)} {file.truncated ? '· (已截断，仅显示前 2MB)' : ''}
              </p>
            </CardHeader>
            <CardContent>
              {file.truncated ? (
                <Alert variant="warning" className="mb-3">
                  <AlertTitle>文件较大</AlertTitle>
                  <AlertDescription>
                    超过 2MB，已截断渲染。完整内容请直接打开本地文件。
                  </AlertDescription>
                </Alert>
              ) : null}
              <MarkdownPreview content={file.parsed.body || file.body} />
            </CardContent>
          </Card>
        ) : null}
      </section>
    </div>
  );
}
