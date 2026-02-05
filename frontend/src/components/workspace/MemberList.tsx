import { Button } from '@/components/ui/button';
import { useWorkspaceMembers, useRemoveWorkspaceMember } from '@/hooks/useWorkspaces';
import type { WorkspaceMember, WorkspaceRole } from '@/types/workspace';

interface MemberListProps {
  workspaceId: string;
  myRole: WorkspaceRole;
  currentUserId: string;
}

const roleLabels: Record<WorkspaceRole, string> = {
  owner: 'Owner',
  editor: 'Editor',
  viewer: 'Viewer',
};

export function MemberList({ workspaceId, myRole, currentUserId }: MemberListProps) {
  const { data: members, isLoading } = useWorkspaceMembers(workspaceId);
  const removeMember = useRemoveWorkspaceMember(workspaceId);

  const canManage = myRole === 'owner';

  const handleRemove = async (member: WorkspaceMember) => {
    if (member.user_id === currentUserId) {
      alert('자기 자신은 제거할 수 없습니다.');
      return;
    }
    if (confirm(`${member.user.name}님을 워크스페이스에서 제거하시겠습니까?`)) {
      await removeMember.mutateAsync(member.user_id);
    }
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">로딩 중...</div>;
  }

  return (
    <div className="space-y-2">
      {members?.map((member) => (
        <div
          key={member.id}
          className="flex items-center justify-between p-3 bg-gray-50 rounded"
        >
          <div>
            <p className="font-medium text-sm">{member.user.name}</p>
            <p className="text-xs text-muted-foreground">{member.user.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-gray-200 px-2 py-1 rounded">
              {roleLabels[member.role]}
            </span>
            {canManage && member.user_id !== currentUserId && (
              <Button
                variant="ghost"
                size="sm"
                className="text-red-500 hover:text-red-700"
                onClick={() => handleRemove(member)}
                disabled={removeMember.isPending}
              >
                제거
              </Button>
            )}
          </div>
        </div>
      ))}
      {members?.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-4">
          멤버가 없습니다.
        </p>
      )}
    </div>
  );
}
