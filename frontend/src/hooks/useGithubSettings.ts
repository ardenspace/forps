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
      // B2: failed git-events 도 refetch (재처리 후 list 갱신)
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'git-events', 'failed'] });
    },
  });
}

// B2 — failed git push events list (TaskCard ⚠️ 와는 별도, 모달 + ProjectItem badge 용)
export function useFailedGitEvents(projectId: string | null) {
  return useQuery({
    queryKey: ['projects', projectId, 'git-events', 'failed'],
    queryFn: () =>
      api.git
        .listGitEvents(projectId!, { failed_only: true, limit: 50 })
        .then((r) => r.data),
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

// Phase 6 — Discord 알림 비활성화 해제 (재활성화 버튼)
export function useResetDiscord(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.git.resetDiscord(projectId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'git-settings'] });
    },
  });
}
