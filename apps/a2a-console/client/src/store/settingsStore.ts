import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SettingsState {
  pollIntervalMs: number;
  setPollInterval: (ms: number) => void;
  agentFilter: string | null;
  setAgentFilter: (id: string | null) => void;
  expertMode: boolean;
  setExpertMode: (enabled: boolean) => void;
  generatorLastSelection: {
    projectType: string;
    generationStrategy: string;
    modelProfile: string;
  };
  setGeneratorLastSelection: (selection: SettingsState['generatorLastSelection']) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      pollIntervalMs: 5000,
      setPollInterval: (ms) => set({ pollIntervalMs: Math.max(1000, ms) }),
      agentFilter: null,
      setAgentFilter: (id) => set({ agentFilter: id }),
      expertMode: false,
      setExpertMode: (enabled) =>
        set((state) => ({
          expertMode: enabled,
          agentFilter: enabled ? state.agentFilter : null,
        })),
      generatorLastSelection: {
        projectType: 'business-dashboard',
        generationStrategy: 'quality',
        modelProfile: 'recommended',
      },
      setGeneratorLastSelection: (selection) => set({ generatorLastSelection: selection }),
    }),
    {
      name: 'a2a-console-settings',
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        pollIntervalMs: s.pollIntervalMs,
        expertMode: s.expertMode === true,
        generatorLastSelection: s.generatorLastSelection,
      }),
      merge: (persisted, current) => {
        const saved = persisted as Partial<SettingsState> | undefined;
        return {
          ...current,
          pollIntervalMs:
            typeof saved?.pollIntervalMs === 'number'
              ? Math.max(1000, saved.pollIntervalMs)
              : current.pollIntervalMs,
          expertMode: saved?.expertMode === true,
          generatorLastSelection: {
            projectType: saved?.generatorLastSelection?.projectType ?? current.generatorLastSelection.projectType,
            generationStrategy:
              saved?.generatorLastSelection?.generationStrategy ?? current.generatorLastSelection.generationStrategy,
            modelProfile: saved?.generatorLastSelection?.modelProfile ?? current.generatorLastSelection.modelProfile,
          },
        };
      },
    },
  ),
);
