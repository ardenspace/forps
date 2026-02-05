import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAddWorkspaceMember } from '@/hooks/useWorkspaces';
import type { WorkspaceRole } from '@/types/workspace';

interface InviteMemberModalProps {
  workspaceId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function InviteMemberModal({ workspaceId, isOpen, onClose }: InviteMemberModalProps) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<WorkspaceRole>('viewer');
  const [error, setError] = useState<string | null>(null);
  const addMember = useAddWorkspaceMember(workspaceId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await addMember.mutateAsync({ email, role });
      setEmail('');
      onClose();
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } };
      if (error.response?.status === 404) {
        setError('해당 이메일의 사용자를 찾을 수 없습니다.');
      } else {
        setError('초대에 실패했습니다. 다시 시도해주세요.');
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">멤버 초대</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">이메일</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">권한</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as WorkspaceRole)}
                className="w-full border rounded px-3 py-2"
              >
                <option value="viewer">Viewer (읽기 전용)</option>
                <option value="editor">Editor (편집 가능)</option>
                <option value="owner">Owner (관리자)</option>
              </select>
            </div>
            {error && (
              <p className="text-sm text-red-500">{error}</p>
            )}
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button type="button" variant="ghost" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={addMember.isPending}>
              {addMember.isPending ? '초대 중...' : '초대'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
