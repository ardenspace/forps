import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { TaskStatus } from '@/types';

interface TaskFilters {
  mineOnly: boolean;
  status: TaskStatus | null;
}

interface UIState {
  selectedWorkspaceId: string | null;
  selectedProjectId: string | null;
  taskFilters: TaskFilters;

  setSelectedWorkspace: (id: string | null) => void;
  setSelectedProject: (id: string | null) => void;
  setTaskFilters: (filters: Partial<TaskFilters>) => void;
  resetTaskFilters: () => void;
}

const defaultFilters: TaskFilters = {
  mineOnly: false,
  status: null,
};

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      selectedWorkspaceId: null,
      selectedProjectId: null,
      taskFilters: defaultFilters,

      setSelectedWorkspace: (id) =>
        set({ selectedWorkspaceId: id, selectedProjectId: null }),
      setSelectedProject: (id) =>
        set({ selectedProjectId: id }),
      setTaskFilters: (filters) =>
        set((state) => ({
          taskFilters: { ...state.taskFilters, ...filters },
        })),
      resetTaskFilters: () =>
        set({ taskFilters: defaultFilters }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        selectedWorkspaceId: state.selectedWorkspaceId,
        selectedProjectId: state.selectedProjectId,
      }),
    }
  )
);
