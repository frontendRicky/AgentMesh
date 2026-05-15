import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/layouts/AppLayout';
import Dashboard from '@/pages/Dashboard';
import Tasks from '@/pages/Tasks';
import TaskDetail from '@/pages/TaskDetail';
import Settings from '@/pages/Settings';
import Blockers from '@/pages/Blockers';
import ModelPrompt from '@/pages/ModelPrompt';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="tasks/:taskId" element={<TaskDetail />} />
          <Route path="settings" element={<Settings />} />
          <Route path="blockers" element={<Blockers />} />
          <Route path="model-prompt" element={<ModelPrompt />} />
          <Route path="artifacts" element={<Navigate to="/tasks" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
