import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import type {
  ErrorGroupAction,
  ErrorGroupStatus,
} from '@/types/error';

interface ListFilters {
  status?: ErrorGroupStatus;
  since?: string;
  offset?: number;
  limit?: number;
}

export function useErrorGroups(projectId: string | null, filters?: ListFilters) {
  return useQuery({
    queryKey: ['projects', projectId, 'errors', filters],
    queryFn: () => api.errors.list(projectId!, filters).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useErrorGroupDetail(projectId: string | null, groupId: string | null) {
  return useQuery({
    queryKey: ['projects', projectId, 'errors', groupId, 'detail'],
    queryFn: () => api.errors.get(projectId!, groupId!).then((r) => r.data),
    enabled: !!projectId && !!groupId,
  });
}

export function useTransitionErrorStatus(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      groupId,
      action,
      resolved_in_version_sha,
    }: {
      groupId: string;
      action: ErrorGroupAction;
      resolved_in_version_sha?: string | null;
    }) =>
      api.errors.transition(projectId, groupId, {
        action,
        resolved_in_version_sha,
      }),
    onSuccess: () => {
      // list + detail 둘 다 invalidate (audit 필드 + status 변경 반영).
      queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'errors'],
      });
    },
  });
}
