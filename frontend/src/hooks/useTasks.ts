import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { TaskCreate, TaskUpdate } from '@/types/task';

interface TaskFilters {
  mine_only?: boolean;
  status?: string;
}

export function useTasks(projectId: string | null, filters?: TaskFilters) {
  return useQuery({
    queryKey: ['projects', projectId, 'tasks', filters],
    queryFn: () => api.tasks.list(projectId!, filters).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useWeekTasks(weekStart: string | null) {
  return useQuery({
    queryKey: ['tasks', 'week', weekStart],
    queryFn: () => api.tasks.getWeek(weekStart!).then((r) => r.data),
    enabled: !!weekStart,
  });
}

export function useTask(id: string | null) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: () => api.tasks.getById(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateTask(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => api.tasks.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: TaskUpdate }) =>
      api.tasks.update(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        predicate: (query) => query.queryKey[2] === 'tasks',
      });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => api.tasks.delete(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        predicate: (query) => query.queryKey[2] === 'tasks',
      });
    },
  });
}
