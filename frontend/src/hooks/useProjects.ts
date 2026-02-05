import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { ProjectCreate } from '@/types/project';

export function useProjects(workspaceId: string | null) {
  return useQuery({
    queryKey: ['workspaces', workspaceId, 'projects'],
    queryFn: () => api.projects.list(workspaceId!).then((r) => r.data),
    enabled: !!workspaceId,
  });
}

export function useProject(id: string | null) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => api.projects.get(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateProject(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => api.projects.create(workspaceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', workspaceId, 'projects'] });
    },
  });
}
