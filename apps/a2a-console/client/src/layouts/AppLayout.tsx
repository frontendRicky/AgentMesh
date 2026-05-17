import { Boxes, FolderKanban, Gauge, ListChecks, MessageCircle, Settings, SlidersHorizontal, WandSparkles } from 'lucide-react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { AgentAvatar } from '@/components/AgentAvatar';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';
import { AGENT_LIST } from '@/constants/agent-meta';
import { useActiveTask, useProjectRoot } from '@/hooks/useActiveTask';
import { useSettingsStore } from '@/store/settingsStore';
import { cn } from '@/lib/cn';

export function AppLayout() {
  const { data: active } = useActiveTask();
  const { data: root } = useProjectRoot();
  const agentFilter = useSettingsStore((s) => s.agentFilter);
  const setAgentFilter = useSettingsStore((s) => s.setAgentFilter);
  const expertMode = useSettingsStore((s) => s.expertMode);
  const setExpertMode = useSettingsStore((s) => s.setExpertMode);
  const navigate = useNavigate();

  function toggleMode() {
    const next = !expertMode;
    setExpertMode(next);
    if (!next) navigate('/generator');
  }

  return (
    <div className="grid h-screen grid-cols-[100px_1fr] grid-rows-[56px_1fr] bg-muted/30">
      <header className="col-span-2 flex items-center justify-between border-b border-border bg-background px-4">
        <div className="flex items-center gap-3">
          <WandSparkles className="h-5 w-5 text-sky-700" />
          <div>
            <h1 className="text-base font-semibold tracking-tight">前端项目生成台</h1>
            <p className="hidden text-[11px] text-muted-foreground sm:block">
              {expertMode ? '专家模式' : '普通模式'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {expertMode ? (
            <div className="hidden items-center gap-3 text-xs text-muted-foreground lg:flex">
              {active?.active_task_id ? (
                <span>
                  当前任务：<code className="text-foreground">{active.active_task_id}</code>
                </span>
              ) : (
                <span className="text-amber-600">未配置当前任务</span>
              )}
              <span className="text-muted-foreground/60">|</span>
              <span className="max-w-[380px] truncate" title={root?.project_root ?? ''}>
                根目录：{root?.project_root ?? '(未配置)'}
              </span>
            </div>
          ) : (
            <p className="hidden text-xs text-muted-foreground md:block">
              用中文整理需求，交给技术同事继续
            </p>
          )}
          <Button variant={expertMode ? 'outline' : 'secondary'} size="sm" onClick={toggleMode}>
            <SlidersHorizontal className="h-4 w-4" />
            {expertMode ? '切到普通模式' : '切到专家模式'}
          </Button>
        </div>
      </header>

      <aside className="row-start-2 flex flex-col items-center gap-4 border-r border-border bg-background py-4">
        {expertMode ? (
          <>
            <div className="flex flex-col items-center gap-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Agents</p>
              {AGENT_LIST.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() =>
                    setAgentFilter(agentFilter === a.id ? null : a.id)
                  }
                  title={`${a.name} · ${a.hint}${agentFilter === a.id ? ' (已过滤)' : ''}`}
                >
                  <AgentAvatar agent={a.id} showName selected={agentFilter === a.id} />
                </button>
              ))}
            </div>
            <div className="mt-auto flex w-full flex-col items-stretch gap-1 border-t border-border px-2 pt-3 text-[11px]">
              <NavItem to="/dashboard" icon={<MessageCircle className="h-4 w-4" />} label="群聊" />
              <NavItem to="/tasks" icon={<ListChecks className="h-4 w-4" />} label="Tasks" />
              <NavItem to="/projects" icon={<FolderKanban className="h-4 w-4" />} label="项目" />
              <NavItem to="/artifacts" icon={<Boxes className="h-4 w-4" />} label="Artifacts" />
              <NavItem to="/model-prompt" icon={<Gauge className="h-4 w-4" />} label="模型" />
              <NavItem to="/settings" icon={<Settings className="h-4 w-4" />} label="设置" />
            </div>
          </>
        ) : (
          <div className="flex w-full flex-col items-stretch gap-1 px-2 text-[11px]">
            <NavItem to="/generator" icon={<WandSparkles className="h-4 w-4" />} label="生成项目" />
            <NavItem to="/tasks" icon={<ListChecks className="h-4 w-4" />} label="我的任务" />
            <NavItem to="/projects" icon={<FolderKanban className="h-4 w-4" />} label="项目" />
            <NavItem to="/settings" icon={<Settings className="h-4 w-4" />} label="设置" />
          </div>
        )}
      </aside>

      <main className="row-start-2 overflow-hidden">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}

function NavItem({
  to,
  icon,
  label,
  end,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  end?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          'flex flex-col items-center gap-0.5 rounded-md px-1 py-1.5 transition-colors',
          isActive ? 'bg-accent text-foreground' : 'text-muted-foreground hover:bg-muted',
        )
      }
    >
      {icon}
      <span className="text-[10px]">{label}</span>
    </NavLink>
  );
}
