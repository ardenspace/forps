import { useState, useRef, useEffect } from 'react';
import { useDeleteProject } from '@/hooks/useProjects';
import { EditProjectModal } from '@/components/sidebar/EditProjectModal';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import type { Project } from '@/types/project';

interface ProjectItemProps {
  project: Project;
  isSelected: boolean;
  workspaceId: string;
  onSelect: (projectId: string) => void;
}

export function ProjectItem({ project, isSelected, workspaceId, onSelect }: ProjectItemProps) {
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const deleteProject = useDeleteProject(workspaceId);

  const isOwner = project.my_role === 'owner';

  useEffect(() => {
    if (!isMenuOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMenuOpen]);

  const handleDelete = async () => {
    await deleteProject.mutateAsync(project.id);
    setDeleteConfirmOpen(false);
  };

  return (
    <li className="group relative">
      <button
        className={`w-full md:w-full whitespace-nowrap md:whitespace-normal text-left px-2 py-1.5 rounded text-xs sm:text-sm font-medium transition-all border-2 ${
          isSelected
            ? 'bg-yellow-400 border-black shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] font-bold'
            : 'border-transparent text-muted-foreground hover:bg-yellow-50 hover:border-black hover:text-foreground'
        }`}
        onClick={() => onSelect(project.id)}
      >
        <span className="truncate block pr-6">{project.name}</span>
      </button>

      {isOwner && (
        <div ref={menuRef}>
          <button
            type="button"
            className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1 text-xs font-bold hover:bg-yellow-100 rounded"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((prev) => !prev);
            }}
          >
            ···
          </button>

          {isMenuOpen && (
            <div className="absolute right-0 top-full mt-1 z-50 min-w-[100px] border-2 border-black bg-white shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]">
              <button
                type="button"
                className="w-full text-left px-3 py-1.5 text-xs font-medium hover:bg-yellow-50 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpen(false);
                  setEditModalOpen(true);
                }}
              >
                수정
              </button>
              <button
                type="button"
                className="w-full text-left px-3 py-1.5 text-xs font-medium hover:bg-yellow-50 transition-colors text-red-600"
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpen(false);
                  setDeleteConfirmOpen(true);
                }}
              >
                삭제
              </button>
            </div>
          )}
        </div>
      )}

      <EditProjectModal
        workspaceId={workspaceId}
        projectId={project.id}
        initialName={project.name}
        initialDescription={project.description ?? ''}
        isOpen={isEditModalOpen}
        onClose={() => setEditModalOpen(false)}
      />

      <ConfirmModal
        isOpen={isDeleteConfirmOpen}
        title="프로젝트 삭제"
        description={`"${project.name}" 프로젝트를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`}
        confirmText="삭제"
        isConfirming={deleteProject.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleteConfirmOpen(false)}
      />
    </li>
  );
}
