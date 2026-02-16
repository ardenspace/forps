import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  useProjectMembers,
  useAddProjectMember,
  useUpdateProjectMemberRole,
  useRemoveProjectMember,
} from '@/hooks/useProjects';
import type { WorkspaceRole } from '@/types/workspace';

interface ProjectMemberManagerProps {
  projectId: string;
  currentUserId: string;
  isOpen: boolean;
  onClose: () => void;
}

const roleOptions: WorkspaceRole[] = ['owner', 'editor', 'viewer'];

export function ProjectMemberManager({
  projectId,
  currentUserId,
  isOpen,
  onClose,
}: ProjectMemberManagerProps) {
  const { data: members, isLoading } = useProjectMembers(isOpen ? projectId : null);
  const addMember = useAddProjectMember(projectId);
  const updateRole = useUpdateProjectMemberRole(projectId);
  const removeMember = useRemoveProjectMember(projectId);

  const [email, setEmail] = useState('');
  const [role, setRole] = useState<WorkspaceRole>('viewer');
  const [error, setError] = useState<string | null>(null);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await addMember.mutateAsync({ email, role });
      setEmail('');
      setRole('viewer');
    } catch (err: unknown) {
      const apiError = err as { response?: { status?: number } };
      if (apiError.response?.status === 404) {
        setError('해당 이메일의 사용자를 찾을 수 없습니다.');
      } else {
        setError('프로젝트 멤버 초대에 실패했습니다.');
      }
    }
  };

  const handleRoleChange = async (userId: string, nextRole: WorkspaceRole) => {
    await updateRole.mutateAsync({ userId, data: { role: nextRole } });
  };

  const handleRemove = async (userId: string, userName: string) => {
    if (userId === currentUserId) {
      alert('자기 자신은 제거할 수 없습니다.');
      return;
    }
    if (!confirm(`${userName}님을 프로젝트에서 제거하시겠습니까?`)) {
      return;
    }
    await removeMember.mutateAsync(userId);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6 w-full max-w-2xl max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-black text-lg">프로젝트 멤버 관리</h2>
          <Button type="button" variant="ghost" onClick={onClose}>닫기</Button>
        </div>

        <form onSubmit={handleInvite} className="border-2 border-black p-3 mb-4 bg-yellow-50">
          <p className="font-bold text-sm mb-2">멤버 초대</p>
          <div className="flex items-center gap-2">
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              required
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as WorkspaceRole)}
              className="h-10 border-2 border-black px-2"
            >
              {roleOptions.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            <Button type="submit" disabled={addMember.isPending}>
              {addMember.isPending ? '초대 중...' : '초대'}
            </Button>
          </div>
          {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
        </form>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">로딩 중...</p>
        ) : (
          <div className="space-y-2">
            {members?.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between border-2 border-black p-3"
              >
                <div>
                  <p className="font-medium text-sm">{member.user.name}</p>
                  <p className="text-xs text-muted-foreground">{member.user.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={member.role}
                    onChange={(e) => handleRoleChange(member.user_id, e.target.value as WorkspaceRole)}
                    className="h-8 border-2 border-black px-2 text-xs"
                    disabled={member.user_id === currentUserId || updateRole.isPending}
                  >
                    {roleOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                  <Button
                    type="button"
                    size="sm"
                    variant="destructive"
                    onClick={() => handleRemove(member.user_id, member.user.name)}
                    disabled={member.user_id === currentUserId || removeMember.isPending}
                  >
                    제거
                  </Button>
                </div>
              </div>
            ))}
            {!members?.length && (
              <p className="text-sm text-muted-foreground text-center py-6">
                프로젝트 멤버가 없습니다.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
