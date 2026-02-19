import { useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';

export function useSendDiscordSummary(workspaceId: string | null) {
  return useMutation({
    mutationFn: () => {
      if (!workspaceId) throw new Error('No workspace selected');
      return api.discord.sendSummary(workspaceId).then((r) => r.data);
    },
  });
}
