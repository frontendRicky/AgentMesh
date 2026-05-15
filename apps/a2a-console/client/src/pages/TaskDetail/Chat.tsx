import { MessagesSquare } from 'lucide-react';

import { Empty } from '@/components/ui/empty';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageCard } from '@/components/MessageCard';
import { useMessages } from '@/hooks/useMessages';
import { useSettingsStore } from '@/store/settingsStore';
import { agentMetaOf } from '@/constants/agent-meta';
import type { CurrentStatus } from '@/types/state';

interface ChatProps {
  taskId: string;
  status: CurrentStatus;
}

export default function Chat({ taskId }: ChatProps) {
  const { data, loading } = useMessages(taskId);
  const agentFilter = useSettingsStore((s) => s.agentFilter);
  const filtered = (data?.items ?? []).filter((m) =>
    agentFilter ? m.from_agent === agentFilter : true,
  );

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="mx-auto max-w-3xl space-y-4 px-5 py-5">
        {agentFilter ? (
          <div className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
            只显示 <strong>{agentMetaOf(agentFilter).name}</strong> 的消息（点左侧头像取消过滤）
          </div>
        ) : null}
        {loading ? (
          <div className="space-y-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex items-start gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-16 w-full rounded-2xl" />
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <Empty
            icon={<MessagesSquare className="h-10 w-10" />}
            title="暂无消息"
            description="等 Agent 开干。每条 handoff / blocker 都会出现在这里。"
          />
        ) : (
          filtered.map((m) => <MessageCard key={m.message_id ?? m.file_path} message={m} taskId={taskId} />)
        )}
      </div>
    </div>
  );
}
