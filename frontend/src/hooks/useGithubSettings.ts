import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { GitSettingsUpdate } from '@/types';

export function useGitSettings(projectId: string | null) {
  return useQuery({
    queryKey: ['projects', projectId, 'git-settings'],
    queryFn: () => api.git.getSettings(projectId!).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useUpdateGitSettings(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GitSettingsUpdate) =>
      api.git.updateSettings(projectId, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'git-settings'] });
    },
  });
}

export function useRegisterWebhook(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.git.registerWebhook(projectId).then((r) => r.data),
    onSuccess: () => {
      // has_webhook_secret 가 true 로 바뀜 — settings 다시 fetch
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'git-settings'] });
    },
  });
}

export function useHandoffs(
  projectId: string | null,
  params?: { branch?: string; limit?: number },
) {
  return useQuery({
    queryKey: ['projects', projectId, 'handoffs', params?.branch ?? 'all', params?.limit ?? 50],
    queryFn: () => api.git.listHandoffs(projectId!, params).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useReprocessEvent(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (eventId: string) =>
      api.git.reprocessEvent(projectId, eventId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'handoffs'] });
    },
  });
}
