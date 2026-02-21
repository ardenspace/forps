import { useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';

export function useSendDiscordSummary(projectId: string | null) {
  return useMutation({
    mutationFn: () => {
      if (!projectId) throw new Error('No project selected');
      return api.discord.sendSummary(projectId).then((r) => r.data);
    },
  });
}
