import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { WorkspaceCreate } from '@/types/workspace';

export function useWorkspaces() {
  return useQuery({
    queryKey: ['workspaces'],
    queryFn: () => api.workspaces.list().then((r) => r.data),
  });
}

export function useWorkspace(id: string | null) {
  return useQuery({
    queryKey: ['workspaces', id],
    queryFn: () => api.workspaces.get(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkspaceCreate) => api.workspaces.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });
}
