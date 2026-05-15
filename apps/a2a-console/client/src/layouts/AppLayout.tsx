import { Settings, ListChecks, MessageCircle, Boxes } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

import { AgentAvatar } from '@/components/AgentAvatar';
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

  return (
    <div className="grid h-screen grid-cols-[100px_1fr] grid-rows-[56px_1fr] bg-muted/30">
      <header className="col-span-2 flex items-center justify-between border-b border-border bg-background px-4">
        <div className="flex items-center gap-3">
          <span className="text-lg" aria-hidden>🤖</span>
          <h1 className="text-base font-semibold tracking-tight">A2A Console</h1>
          <span className="rounded bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">MVP</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {active?.active_task_id ? (
            <span>
              当前 Task：<code className="text-foreground">{active.active_task_id}</code>
            </span>
          ) : (
            <span className="text-amber-600">未配置 active task</span>
          )}
          <span className="hidden text-muted-foreground/60 md:inline">|</span>
          <span className="hidden truncate max-w-[400px] md:inline" title={root?.project_root ?? ''}>
            根目录：{root?.project_root ?? '(未配置)'}
          </span>
        </div>
      </header>

      <aside className="row-start-2 flex flex-col items-center gap-4 border-r border-border bg-background py-4">
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
          <NavItem to="/" icon={<MessageCircle className="h-4 w-4" />} label="群聊" end />
          <NavItem to="/tasks" icon={<ListChecks className="h-4 w-4" />} label="Tasks" />
          <NavItem to="/artifacts" icon={<Boxes className="h-4 w-4" />} label="Artifacts" />
          <NavItem to="/settings" icon={<Settings className="h-4 w-4" />} label="设置" />
        </div>
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
