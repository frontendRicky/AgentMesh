import { ModelSelector } from '@/components/ModelSelector';
import { PromptKeywordCard } from '@/components/PromptKeywordCard';
import { useModelPresets } from '@/hooks/useModelPresets';
import { usePromptKeywords } from '@/hooks/usePromptKeywords';
import type { CurrentStatus } from '@/types/state';
import { Skeleton } from '@/components/ui/skeleton';

interface Props {
  taskId: string;
  status: CurrentStatus;
}

export default function ModelPromptTab({ taskId, status }: Props) {
  const { data: presets, loading: presetsLoading } = useModelPresets(taskId);
  const { data: kw } = usePromptKeywords(taskId);

  return (
    <div className="grid gap-4 px-5 py-5 lg:grid-cols-[1fr_360px]">
      {presetsLoading ? <Skeleton className="h-64 w-full" /> : (
        <ModelSelector presets={presets?.entries ?? []} />
      )}
      <PromptKeywordCard status={status} hint={kw?.hint} />
    </div>
  );
}
