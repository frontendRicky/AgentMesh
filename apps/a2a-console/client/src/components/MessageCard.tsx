import { useState } from 'react';

import { AgentAvatar } from './AgentAvatar';
import { MessageTypeBadge } from './StatusBadge';
import { MarkdownPreview } from './MarkdownPreview';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { agentMetaOf } from '@/constants/agent-meta';
import { useArtifactFile } from '@/hooks/useArtifact';
import { cn } from '@/lib/cn';
import { formatRelative, formatTime } from '@/lib/format';
import type { MessageItem } from '@/types/message';

interface MessageCardProps {
  message: MessageItem;
  taskId: string;
}

export function MessageCard({ message, taskId }: MessageCardProps) {
  const [open, setOpen] = useState(false);
  const meta = agentMetaOf(message.from_agent);

  return (
    <>
      <div className="flex items-start gap-3">
        <AgentAvatar agent={message.from_agent} size="sm" />
        <div className="flex-1 min-w-0">
          <div className="mb-1 flex flex-wrap items-baseline gap-2">
            <span className="text-xs font-semibold text-foreground">{meta.name}</span>
            <MessageTypeBadge type={message.message_type ?? null} />
            <span className="text-[10px] text-muted-foreground" title={formatTime(message.created_at)}>
              {formatRelative(message.created_at)}
            </span>
            {message.to_agent ? (
              <span className="text-[10px] text-muted-foreground">→ {agentMetaOf(message.to_agent).name}</span>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => setOpen(true)}
            className={cn(
              'group block w-full rounded-2xl border px-4 py-3 text-left transition-shadow hover:shadow-sm',
              meta.bubbleClass,
            )}
          >
            {message.intent ? (
              <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-foreground/60">
                {message.intent}
              </div>
            ) : null}
            <p className="text-sm leading-relaxed text-foreground/90">
              {message.summary ?? '(无 summary，点击查看详情)'}
            </p>
            {message.referenced_artifacts.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {message.referenced_artifacts.slice(0, 6).map((art) => (
                  <span
                    key={art}
                    className="rounded bg-background/60 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                  >
                    📎 {art}
                  </span>
                ))}
                {message.referenced_artifacts.length > 6 ? (
                  <span className="text-[10px] text-muted-foreground">
                    +{message.referenced_artifacts.length - 6} more
                  </span>
                ) : null}
              </div>
            ) : null}
            <div className="mt-2 text-[10px] text-muted-foreground/70 group-hover:text-muted-foreground">
              点击展开完整 markdown
            </div>
          </button>
        </div>
      </div>
      <MessageDetailDialog
        open={open}
        onOpenChange={setOpen}
        message={message}
        taskId={taskId}
      />
    </>
  );
}

function MessageDetailDialog({
  open,
  onOpenChange,
  message,
  taskId,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  message: MessageItem;
  taskId: string;
}) {
  const { data, error, loading } = useArtifactFile(open ? taskId : null, open ? message.file_path : null);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {agentMetaOf(message.from_agent).name} · {message.intent ?? message.message_type ?? 'message'}
          </DialogTitle>
          <DialogDescription>
            {message.file_path} · {formatTime(message.created_at)}
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[60vh] overflow-auto scrollbar-thin pr-2">
          {loading ? (
            <p className="text-sm text-muted-foreground">加载中...</p>
          ) : error ? (
            <p className="text-sm text-destructive">读取失败：{error.message}</p>
          ) : data ? (
            <MarkdownPreview content={data.parsed.body || data.body} />
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
