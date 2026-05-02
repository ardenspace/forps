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
    <div className="fixed inset-0 bg-brand-coffee/20 backdrop-blur-sm flex items-center justify-center z-50 p-3 sm:p-4">
      <div className="bg-brand-cream rounded-3xl shadow-xl border border-brand-blue/10 w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col p-4 sm:p-6">
        <h2 className="font-bold text-base text-brand-blue sm:text-lg mb-4 shrink-0">새 프로젝트</h2>
        
        <div className="overflow-y-auto w-full flex-1 min-h-0 pr-2 -mr-2">
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="font-bold text-sm block mb-1">프로젝트 이름 *</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="프로젝트 이름"
                  required
                  className="border border-brand-blue/20 rounded-xl w-full px-3 py-2 text-sm focus:outline-none focus:shadow-sm"
                />
              </div>
              <div>
                <label className="font-bold text-sm block mb-1">설명</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="프로젝트 설명 (선택)"
                  className="border border-brand-blue/20 rounded-xl w-full px-3 py-2 text-sm focus:outline-none focus:shadow-sm min-h-[80px] resize-none"
                />
              </div>
            </div>
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="border border-brand-blue/20 font-bold px-4 py-2 text-xs sm:text-sm hover:bg-white/60 transition-colors w-full sm:w-auto"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={createProject.isPending}
                className="bg-brand-blue text-white border border-brand-blue/20 font-bold px-4 py-2 text-xs sm:text-sm hover:bg-brand-neon hover:text-brand-blue transition-colors shadow-sm disabled:opacity-50 w-full sm:w-auto"
              >
                {createProject.isPending ? '생성 중...' : '생성'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
