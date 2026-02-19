import { useState } from 'react';
import { useUpdateProject } from '@/hooks/useProjects';

interface EditProjectModalProps {
  workspaceId: string;
  projectId: string;
  initialName: string;
  initialDescription: string;
  isOpen: boolean;
  onClose: () => void;
}

export function EditProjectModal({
  workspaceId,
  projectId,
  initialName,
  initialDescription,
  isOpen,
  onClose,
}: EditProjectModalProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const updateProject = useUpdateProject(workspaceId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProject.mutateAsync({
      projectId,
      data: { name, description: description || undefined },
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-3 sm:p-4">
      <div className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-4 sm:p-6 w-full max-w-md max-h-[90vh] overflow-auto">
        <h2 className="font-black text-base sm:text-lg mb-4">프로젝트 수정</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="font-bold text-sm block mb-1">프로젝트 이름 *</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="프로젝트 이름"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">설명</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="프로젝트 설명 (선택)"
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] min-h-[80px] resize-none"
              />
            </div>
          </div>
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="border-2 border-black font-bold px-4 py-2 text-xs sm:text-sm hover:bg-yellow-100 transition-colors w-full sm:w-auto"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={updateProject.isPending}
              className="bg-black text-white border-2 border-black font-bold px-4 py-2 text-xs sm:text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] disabled:opacity-50 w-full sm:w-auto"
            >
              {updateProject.isPending ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
