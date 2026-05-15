import { Link } from 'react-router-dom';

import { Empty } from '@/components/ui/empty';
import { Button } from '@/components/ui/button';
import { useActiveTask } from '@/hooks/useActiveTask';
import { useModelPresets } from '@/hooks/useModelPresets';
import { usePromptKeywords } from '@/hooks/usePromptKeywords';
import { ModelSelector } from '@/components/ModelSelector';
import { PromptKeywordCard } from '@/components/PromptKeywordCard';
import { useTaskDetail } from '@/hooks/useTaskDetail';
import type { CurrentStatus } from '@/types/state';

export default function ModelPromptPage() {
  const { data: active } = useActiveTask();
  const taskId = active?.active_task_id ?? null;
  const { data: detail } = useTaskDetail(taskId);
  const { data: presets } = useModelPresets(taskId);
  const { data: kw } = usePromptKeywords(taskId);

  if (!taskId) {
    return (
      <div className="p-6">
        <Empty title="无 active task" action={<Button asChild size="sm"><Link to="/tasks">查看 Tasks</Link></Button>} />
      </div>
    );
  }
  const status = (detail?.state.current_status as CurrentStatus) ?? 'created';
  return (
    <div className="grid gap-4 px-5 py-5 lg:grid-cols-[1fr_360px]">
      <ModelSelector presets={presets?.entries ?? []} />
      <PromptKeywordCard status={status} hint={kw?.hint} />
    </div>
  );
}
