import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { AGENT_LIST, type AgentId } from '@/constants/agent-meta';
import { MODEL_OPTIONS } from '@/constants/model-context';
import { useModelStore } from '@/store/modelStore';
import type { ModelPresetEntry } from '@/hooks/useModelPresets';

interface ModelSelectorProps {
  presets: ModelPresetEntry[];
}

export function ModelSelector({ presets }: ModelSelectorProps) {
  const selections = useModelStore((s) => s.selections);
  const setSelection = useModelStore((s) => s.setSelection);
  const presetMap = new Map(presets.map((p) => [p.agent, p]));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model 选择</CardTitle>
        <CardDescription>
          仅用于本地展示与下次调起 Agent 时的提示。Console 不会替你调用模型 API。
          Override 来自 <code className="text-[11px]">.ai-agents/agent-cards/model-overrides.md</code>。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {AGENT_LIST.filter((a) => a.id !== 'human' && a.id !== 'controller').map((agent) => {
          const preset = presetMap.get(agent.id);
          const localPick = selections[agent.id as AgentId];
          const hasOverride = preset?.source === 'override';
          return (
            <div key={agent.id} className="grid grid-cols-[120px_1fr_auto] items-center gap-3">
              <div className="flex items-center gap-2">
                <span aria-hidden>{agent.emoji}</span>
                <span className="text-sm font-medium">{agent.name}</span>
              </div>
              <Select
                value={localPick ?? preset?.model ?? ''}
                onValueChange={(v) => setSelection(agent.id as AgentId, v || null)}
                disabled={hasOverride}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="(未选择，调起时弹窗询问)" />
                </SelectTrigger>
                <SelectContent>
                  {MODEL_OPTIONS.map((m) => (
                    <SelectItem key={m.slug} value={m.slug}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="text-[10px] text-muted-foreground">
                {hasOverride ? (
                  <Badge variant="outline" className="text-[10px]">override 锁定</Badge>
                ) : localPick ? (
                  <Badge variant="secondary" className="text-[10px]">本地已选</Badge>
                ) : (
                  <Badge variant="outline" className="text-[10px]">未选</Badge>
                )}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
