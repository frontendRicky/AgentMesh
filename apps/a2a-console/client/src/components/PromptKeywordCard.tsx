import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from '@/components/ui/sonner';
import { PROMPT_KEYWORDS } from '@/constants/prompt-keywords';
import type { CurrentStatus } from '@/types/state';
import { cn } from '@/lib/cn';

interface PromptKeywordCardProps {
  status: CurrentStatus;
  hint?: string | null;
  className?: string;
}

export function PromptKeywordCard({ status, hint, className }: PromptKeywordCardProps) {
  const [copied, setCopied] = useState(false);
  const entry = PROMPT_KEYWORDS[status];
  const finalHint = hint ?? entry.hint ?? null;

  async function copy() {
    if (!entry.keyword) return;
    try {
      await navigator.clipboard.writeText(entry.keyword);
      setCopied(true);
      toast.success(`已复制：${entry.keyword}`);
      window.setTimeout(() => setCopied(false), 1500);
    } catch (e) {
      toast.error('复制失败：' + String(e));
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          下一步关键字
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div>
          <span
            className={cn(
              'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium',
              entry.badgeClass,
            )}
          >
            {entry.badgeText}
          </span>
        </div>
        {entry.keyword ? (
          <div className="flex items-center gap-2">
            <code className="flex-1 truncate rounded bg-muted px-2 py-1 text-xs">
              {entry.keyword}
            </code>
            <Button size="xs" variant="outline" onClick={copy}>
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              <span>复制</span>
            </Button>
          </div>
        ) : null}
        {finalHint ? (
          <p className="text-xs text-muted-foreground">{finalHint}</p>
        ) : null}
        <p className="text-[10px] text-muted-foreground/70">
          复制后到 Cursor 粘贴。Console 不会自动调起 Agent。
        </p>
      </CardContent>
    </Card>
  );
}
