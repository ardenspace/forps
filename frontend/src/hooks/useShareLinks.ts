import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { ShareLinkCreateRequest } from '@/types';

export function useShareLinks(projectId: string | null) {
  return useQuery({
    queryKey: ['projects', projectId, 'share-links'],
    queryFn: () => api.shareLinks.list(projectId!).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useCreateShareLink(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data?: ShareLinkCreateRequest) => api.shareLinks.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'share-links'] });
    },
  });
}

export function useDeactivateShareLink(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (shareLinkId: string) => api.shareLinks.deactivate(shareLinkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'share-links'] });
    },
  });
}

export function useActivateShareLink(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (shareLinkId: string) => api.shareLinks.activate(shareLinkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'share-links'] });
    },
  });
}

export function useDeleteShareLink(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (shareLinkId: string) => api.shareLinks.delete(shareLinkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'share-links'] });
    },
  });
}
