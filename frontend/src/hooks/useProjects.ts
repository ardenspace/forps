import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { ProjectCreate, AddProjectMemberRequest, UpdateProjectMemberRequest } from '@/types/project';

export function useProjects(workspaceId: string | null) {
  return useQuery({
    queryKey: ['workspaces', workspaceId, 'projects'],
    queryFn: () => api.projects.list(workspaceId!).then((r) => r.data),
    enabled: !!workspaceId,
  });
}

export function useMyProjects() {
  return useQuery({
    queryKey: ['projects', 'mine'],
    queryFn: () => api.projects.listMine().then((r) => r.data),
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
      queryClient.invalidateQueries({ queryKey: ['projects', 'mine'] });
    },
  });
}

export function useUpdateProject(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: { name?: string; description?: string } }) =>
      api.projects.update(workspaceId, projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', workspaceId, 'projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'mine'] });
    },
  });
}

export function useDeleteProject(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => api.projects.delete(workspaceId, projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', workspaceId, 'projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'mine'] });
    },
  });
}

export function useProjectMembers(projectId: string | null) {
  return useQuery({
    queryKey: ['projects', projectId, 'members'],
    queryFn: () => api.projects.getMembers(projectId!).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useAddProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AddProjectMemberRequest) => api.projects.addMember(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] });
    },
  });
}

export function useUpdateProjectMemberRole(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UpdateProjectMemberRequest }) =>
      api.projects.updateMemberRole(projectId, userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] });
    },
  });
}

export function useRemoveProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => api.projects.removeMember(projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] });
    },
  });
}
