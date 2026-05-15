import { AlertTriangle } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { BlockerItem } from '@/types/blocker';
import { formatTime } from '@/lib/format';

export function BlockerCard({ blocker }: { blocker: BlockerItem }) {
  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>{blocker.blocker_id ?? '阻塞中'}</AlertTitle>
      <AlertDescription>
        <div className="space-y-1">
          {blocker.blocking_reason ? (
            <p>
              <span className="font-medium">原因：</span> {blocker.blocking_reason}
            </p>
          ) : null}
          {blocker.required_fix ? (
            <p>
              <span className="font-medium">修复：</span> {blocker.required_fix}
            </p>
          ) : null}
          {blocker.missing_artifacts.length > 0 ? (
            <p>
              <span className="font-medium">缺失：</span> {blocker.missing_artifacts.join(', ')}
            </p>
          ) : null}
          {blocker.resume_to_agent ? (
            <p>
              <span className="font-medium">恢复到：</span> {blocker.resume_to_agent} ({blocker.resume_to_status ?? '—'})
            </p>
          ) : null}
          <p className="text-[10px] opacity-70">{formatTime(blocker.created_at)} · {blocker.file_path}</p>
        </div>
      </AlertDescription>
    </Alert>
  );
}
