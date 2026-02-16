import { useState } from 'react';
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
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6 w-full max-w-md">
        <h2 className="font-black text-lg mb-4">새 프로젝트</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="font-bold text-sm block mb-1">프로젝트 이름 *</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="프로젝트 이름"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              />
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">설명</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="프로젝트 설명 (선택)"
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] min-h-[80px] resize-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-100 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={createProject.isPending}
              className="bg-black text-white border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50"
            >
              {createProject.isPending ? '생성 중...' : '생성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
