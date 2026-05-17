import type { ReactNode } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/layouts/AppLayout';
import Dashboard from '@/pages/Dashboard';
import Generator from '@/pages/Generator';
import Projects from '@/pages/Projects';
import Tasks from '@/pages/Tasks';
import TaskDetail from '@/pages/TaskDetail';
import Settings from '@/pages/Settings';
import Blockers from '@/pages/Blockers';
import ModelPrompt from '@/pages/ModelPrompt';
import { useSettingsStore } from '@/store/settingsStore';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/generator" replace />} />
          <Route path="generator" element={<Generator />} />
          <Route path="projects" element={<Projects />} />
          <Route path="dashboard" element={<ExpertOnly><Dashboard /></ExpertOnly>} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="tasks/:taskId" element={<TaskDetail />} />
          <Route path="settings" element={<Settings />} />
          <Route path="blockers" element={<ExpertOnly><Blockers /></ExpertOnly>} />
          <Route path="model-prompt" element={<ExpertOnly><ModelPrompt /></ExpertOnly>} />
          <Route path="artifacts" element={<ExpertOnly><Navigate to="/tasks" replace /></ExpertOnly>} />
          <Route path="*" element={<Navigate to="/generator" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function ExpertOnly({ children }: { children: ReactNode }) {
  const expertMode = useSettingsStore((s) => s.expertMode);
  if (!expertMode) return <Navigate to="/generator" replace />;
  return <>{children}</>;
}
