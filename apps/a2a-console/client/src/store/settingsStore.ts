import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SettingsState {
  pollIntervalMs: number;
  setPollInterval: (ms: number) => void;
  agentFilter: string | null;
  setAgentFilter: (id: string | null) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      pollIntervalMs: 5000,
      setPollInterval: (ms) => set({ pollIntervalMs: Math.max(1000, ms) }),
      agentFilter: null,
      setAgentFilter: (id) => set({ agentFilter: id }),
    }),
    {
      name: 'a2a-console-settings',
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ pollIntervalMs: s.pollIntervalMs }),
    },
  ),
);
