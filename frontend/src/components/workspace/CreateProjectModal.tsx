import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCreateProject } from '@/hooks/useProjects';

interface CreateProjectModalProps {
  workspaceId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function CreateProjectModal({ workspaceId, isOpen, onClose }: CreateProjectModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const createProject = useCreateProject(workspaceId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createProject.mutateAsync({
      name,
      description: description || undefined,
    });
    setName('');
    setDescription('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">새 프로젝트</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">프로젝트 이름 *</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="프로젝트 이름"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">설명</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="프로젝트 설명 (선택)"
                className="w-full border rounded px-3 py-2 text-sm min-h-[80px]"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button type="button" variant="ghost" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? '생성 중...' : '생성'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
