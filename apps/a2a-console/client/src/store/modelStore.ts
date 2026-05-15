import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type { AgentId } from '@/constants/agent-meta';

interface ModelState {
  selections: Partial<Record<AgentId, string>>;
  setSelection: (agent: AgentId, model: string | null) => void;
}

export const useModelStore = create<ModelState>()(
  persist(
    (set) => ({
      selections: {},
      setSelection: (agent, model) =>
        set((state) => {
          const next = { ...state.selections };
          if (!model) delete next[agent];
          else next[agent] = model;
          return { selections: next };
        }),
    }),
    {
      name: 'a2a-console-model-selections',
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
