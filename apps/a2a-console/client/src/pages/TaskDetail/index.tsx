import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Empty } from '@/components/ui/empty';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/StatusBadge';
import { MiniTimeline } from '@/components/TimelineNode';
import { apiGet, apiPost } from '@/hooks/useApi';
import { useTaskDetail } from '@/hooks/useTaskDetail';
import { useBlockers } from '@/hooks/useBlockers';
import { useSettingsStore } from '@/store/settingsStore';
import { agentMetaOf } from '@/constants/agent-meta';
import { cn } from '@/lib/cn';
import type { ArtifactFile } from '@/types/artifact';
import type { CurrentStatus } from '@/types/state';

import Chat from './Chat';
import OrdinaryView from './OrdinaryView';
import Overview from './Overview';
import Timeline from './Timeline';
import Artifacts from './Artifacts';
import Risk from './Risk';
import Metrics from './Metrics';
import ModelPromptTab from './ModelPromptTab';
import SandboxTab from './SandboxTab';

export default function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const { data, error, loading } = useTaskDetail(taskId ?? null);
  const { data: blockers } = useBlockers(taskId ?? null);
  const expertMode = useSettingsStore((s) => s.expertMode);
  const policyDecision = usePolicyDecision(taskId ?? null, expertMode);
  const contextPack = useContextPack(taskId ?? null, expertMode, data?.state.current_agent);

  if (!taskId) {
    return <div className="p-6">缺少 taskId 参数</div>;
  }

  if (loading) {
    return (
      <div className="space-y-3 p-6">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="p-6">
        <Empty
          title={`加载失败 (${error.code})`}
          description={error.message}
          action={
            <Button asChild size="sm" variant="outline">
              <Link to="/tasks">返回列表</Link>
            </Button>
          }
        />
      </div>
    );
  }
  if (!data) return null;

  if (!expertMode) {
    return <OrdinaryView taskId={taskId} data={data} />;
  }

  const status = data.state.current_status as CurrentStatus;
  const isBlocked = (blockers?.items?.length ?? 0) > 0;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="border-b border-border bg-background px-5 py-3">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Button asChild variant="ghost" size="icon" className="h-7 w-7">
                <Link to="/tasks"><ArrowLeft className="h-4 w-4" /></Link>
              </Button>
              <h2 className="truncate text-base font-semibold">
                {data.task.task_title} <span className="ml-1 font-mono text-[11px] text-muted-foreground">{taskId}</span>
              </h2>
              <StatusBadge status={status} />
            </div>
            <p className="mt-0.5 pl-9 text-[11px] text-muted-foreground">
              当前 {agentMetaOf(data.state.current_agent).name} · 下一棒 {agentMetaOf(data.state.next_agent).name} · 更新于 {data.state.updated_at}
            </p>
          </div>
          <ExpertSideCards policyDecision={policyDecision} contextPack={contextPack} />
        </div>
        <div className="mt-3">
          <MiniTimeline current={status} isBlocked={isBlocked} />
        </div>
      </header>

      <Tabs defaultValue="chat" className="flex flex-1 flex-col overflow-hidden">
        <div className="border-b border-border bg-background px-5">
          <TabsList className="bg-transparent p-0 h-auto gap-3 mt-0">
            <TabsTrigger value="chat" className="data-[state=active]:bg-muted">💬 群聊</TabsTrigger>
            <TabsTrigger value="overview" className="data-[state=active]:bg-muted">概览</TabsTrigger>
            <TabsTrigger value="timeline" className="data-[state=active]:bg-muted">时间线</TabsTrigger>
            <TabsTrigger value="artifacts" className="data-[state=active]:bg-muted">Artifacts</TabsTrigger>
            <TabsTrigger value="risk" className="data-[state=active]:bg-muted">
              风险/Blocker
              {isBlocked ? <span className="ml-1 rounded bg-red-500 px-1 text-[10px] text-white">{blockers?.items.length}</span> : null}
            </TabsTrigger>
            <TabsTrigger value="metrics" className="data-[state=active]:bg-muted">指标</TabsTrigger>
            <TabsTrigger value="model" className="data-[state=active]:bg-muted">Model & Prompt</TabsTrigger>
            <TabsTrigger value="sandbox" className="data-[state=active]:bg-muted">Sandbox</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-hidden">
          <TabsContent value="chat" className="h-full mt-0"><Chat taskId={taskId} status={status} /></TabsContent>
          <TabsContent value="overview" className="h-full mt-0 overflow-y-auto scrollbar-thin"><Overview detail={data} /></TabsContent>
          <TabsContent value="timeline" className="h-full mt-0 overflow-y-auto scrollbar-thin"><Timeline taskId={taskId} /></TabsContent>
          <TabsContent value="artifacts" className="h-full mt-0"><Artifacts taskId={taskId} /></TabsContent>
          <TabsContent value="risk" className="h-full mt-0 overflow-y-auto scrollbar-thin"><Risk taskId={taskId} /></TabsContent>
          <TabsContent value="metrics" className="h-full mt-0 overflow-y-auto scrollbar-thin"><Metrics taskId={taskId} /></TabsContent>
          <TabsContent value="model" className="h-full mt-0 overflow-y-auto scrollbar-thin"><ModelPromptTab taskId={taskId} status={status} /></TabsContent>
          <TabsContent value="sandbox" className="h-full mt-0"><SandboxTab taskId={taskId} /></TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

interface ContextPack {
  pack_id: string;
  task_id: string;
  agent: 'pm' | 'architect' | 'developer' | 'qa' | 'fix' | 'security';
  items: Array<{
    type: string;
    inclusion_reason: string;
    estimated_tokens: number;
    truncated: boolean;
  }>;
  total_estimated_input_tokens: number;
  full_context: boolean;
  created_at: string;
}

interface PolicyDecision {
  decision: 'AUTO_APPROVE' | 'AUTO_REJECT' | 'NEED_HUMAN_REVIEW' | 'NEED_MORE_TESTS' | 'NEED_FIX_LOOP';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  reasons: string[];
  matched_rules: string[];
  evaluated_paths: Array<{ path: string; risk: string }>;
  budget_status: 'ok' | 'warning' | 'breached';
  created_at: string;
}

function usePolicyDecision(taskId: string | null, enabled: boolean): PolicyDecision | null {
  const [decision, setDecision] = useState<PolicyDecision | null>(null);

  useEffect(() => {
    if (!taskId || !enabled) {
      setDecision(null);
      return;
    }

    let cancelled = false;
    const artifactPath = 'artifacts/architect/file-change-plan.md';
    apiGet<ArtifactFile>(
      `/api/a2a/tasks/${taskId}/artifacts?path=${encodeURIComponent(artifactPath)}`,
    )
      .then((artifact) => apiPost<unknown>('/api/a2a/policy/evaluate', {
        task_id: taskId,
        file_change_plan_text: artifact.body,
      }))
      .then((raw) => {
        if (cancelled) return;
        setDecision(isPolicyDecision(raw) ? raw : null);
      })
      .catch(() => {
        if (!cancelled) setDecision(null);
      });

    return () => {
      cancelled = true;
    };
  }, [taskId, enabled]);

  return decision;
}

function useContextPack(taskId: string | null, enabled: boolean, currentAgent: unknown): ContextPack | null {
  const [pack, setPack] = useState<ContextPack | null>(null);

  useEffect(() => {
    const agent = mapContextAgent(currentAgent);
    if (!taskId || !enabled || !agent) {
      setPack(null);
      return;
    }

    let cancelled = false;
    apiPost<unknown>('/api/a2a/context/build', {
      task_id: taskId,
      agent,
    })
      .then((raw) => {
        if (cancelled) return;
        setPack(isContextPack(raw) ? raw : null);
      })
      .catch(() => {
        if (!cancelled) setPack(null);
      });

    return () => {
      cancelled = true;
    };
  }, [taskId, enabled, currentAgent]);

  return pack;
}

function ExpertSideCards({
  policyDecision,
  contextPack,
}: {
  policyDecision: PolicyDecision | null;
  contextPack: ContextPack | null;
}) {
  if (!policyDecision && !contextPack) return null;
  return (
    <div className="hidden w-[320px] shrink-0 flex-col gap-2 lg:flex">
      {policyDecision ? <PolicySuggestionCard decision={policyDecision} /> : null}
      {contextPack ? <ContextEstimateCard pack={contextPack} /> : null}
    </div>
  );
}

function PolicySuggestionCard({ decision }: { decision: PolicyDecision }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium">Policy 建议</p>
        <Badge variant="outline" className={cn('font-mono', riskBadgeClass(decision.risk_level))}>
          {decision.decision}
        </Badge>
      </div>
      <p className="mt-1 text-[11px] text-muted-foreground">
        risk: {decision.risk_level} · budget: {decision.budget_status}
      </p>
      <ul className="mt-2 space-y-1 text-[11px] text-muted-foreground">
        {decision.reasons.slice(0, 3).map((reason) => (
          <li key={reason} className="line-clamp-2">{reason}</li>
        ))}
      </ul>
    </div>
  );
}

function ContextEstimateCard({ pack }: { pack: ContextPack }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium">Context 估算</p>
        <Badge variant="outline" className="font-mono">
          {pack.total_estimated_input_tokens}
        </Badge>
      </div>
      <p className="mt-1 text-[11px] text-muted-foreground">
        {pack.agent} · {pack.items.length} items
      </p>
      <ul className="mt-2 space-y-1 text-[11px] text-muted-foreground">
        {pack.items.slice(0, 3).map((item) => (
          <li key={`${item.type}-${item.inclusion_reason}`} className="line-clamp-2">
            {item.inclusion_reason}
          </li>
        ))}
      </ul>
    </div>
  );
}

function riskBadgeClass(risk: PolicyDecision['risk_level']): string {
  if (risk === 'critical') return 'border-red-300 bg-red-50 text-red-700';
  if (risk === 'high') return 'border-amber-300 bg-amber-50 text-amber-700';
  if (risk === 'medium') return 'border-sky-300 bg-sky-50 text-sky-700';
  return 'border-emerald-300 bg-emerald-50 text-emerald-700';
}

function isPolicyDecision(value: unknown): value is PolicyDecision {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    isDecision(record['decision'])
    && isRiskLevel(record['risk_level'])
    && Array.isArray(record['reasons'])
    && record['reasons'].every((reason) => typeof reason === 'string')
    && Array.isArray(record['matched_rules'])
    && record['matched_rules'].every((rule) => typeof rule === 'string')
    && Array.isArray(record['evaluated_paths'])
    && isBudgetStatus(record['budget_status'])
    && typeof record['created_at'] === 'string'
  );
}

function isDecision(value: unknown): value is PolicyDecision['decision'] {
  return (
    value === 'AUTO_APPROVE'
    || value === 'AUTO_REJECT'
    || value === 'NEED_HUMAN_REVIEW'
    || value === 'NEED_MORE_TESTS'
    || value === 'NEED_FIX_LOOP'
  );
}

function isRiskLevel(value: unknown): value is PolicyDecision['risk_level'] {
  return value === 'low' || value === 'medium' || value === 'high' || value === 'critical';
}

function isBudgetStatus(value: unknown): value is PolicyDecision['budget_status'] {
  return value === 'ok' || value === 'warning' || value === 'breached';
}

function mapContextAgent(value: unknown): ContextPack['agent'] | null {
  if (value === 'pm') return 'pm';
  if (value === 'architect') return 'architect';
  if (value === 'developer') return 'developer';
  if (value === 'qa') return 'qa';
  if (value === 'controller' || value === 'human') return 'qa';
  return null;
}

function isContextPack(value: unknown): value is ContextPack {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record['pack_id'] === 'string'
    && typeof record['task_id'] === 'string'
    && isContextAgent(record['agent'])
    && Array.isArray(record['items'])
    && record['items'].every(isContextPackItem)
    && typeof record['total_estimated_input_tokens'] === 'number'
    && typeof record['full_context'] === 'boolean'
    && typeof record['created_at'] === 'string'
  );
}

function isContextPackItem(value: unknown): value is ContextPack['items'][number] {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record['type'] === 'string'
    && typeof record['inclusion_reason'] === 'string'
    && typeof record['estimated_tokens'] === 'number'
    && typeof record['truncated'] === 'boolean'
  );
}

function isContextAgent(value: unknown): value is ContextPack['agent'] {
  return (
    value === 'pm'
    || value === 'architect'
    || value === 'developer'
    || value === 'qa'
    || value === 'fix'
    || value === 'security'
  );
}
