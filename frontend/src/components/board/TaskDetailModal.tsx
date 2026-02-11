import { useState, useEffect, useRef } from 'react';
import { useUpdateTask } from '@/hooks/useTasks';
import type { Task, TaskStatus } from '@/types/task';
import type { WorkspaceRole, WorkspaceMember } from '@/types/workspace';

interface TaskDetailModalProps {
  task: Task | null;
  myRole: WorkspaceRole;
  members: WorkspaceMember[];
  isOpen: boolean;
  onClose: () => void;
  onDelete?: (taskId: string) => void;
}

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'todo', label: 'To Do' },
  { value: 'doing', label: 'Doing' },
  { value: 'done', label: 'Done' },
  { value: 'blocked', label: 'Blocked' },
];

export function TaskDetailModal({ task, myRole, members, isOpen, onClose, onDelete }: TaskDetailModalProps) {
  const updateTask = useUpdateTask();
  const modalRef = useRef<HTMLDivElement>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<TaskStatus>('todo');
  const [dueDate, setDueDate] = useState('');
  const [assigneeId, setAssigneeId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [showSaved, setShowSaved] = useState(false);

  const [original, setOriginal] = useState({
    title: '',
    description: '',
    status: 'todo' as TaskStatus,
    dueDate: '',
    assigneeId: null as string | null,
  });

  useEffect(() => {
    if (task && isOpen) {
      const taskDueDate = task.due_date ? task.due_date.split('T')[0] : '';
      setTitle(task.title);
      setDescription(task.description || '');
      setStatus(task.status);
      setDueDate(taskDueDate);
      setAssigneeId(task.assignee_id);
      setOriginal({
        title: task.title,
        description: task.description || '',
        status: task.status,
        dueDate: taskDueDate,
        assigneeId: task.assignee_id,
      });
      setIsSaving(false);
      setShowSaved(false);
    }
  }, [task, isOpen]);

  const canEdit = myRole === 'owner' || myRole === 'editor';
  const canDelete = myRole === 'owner';

  if (!isOpen || !task) return null;

  const hasChanges =
    title !== original.title ||
    description !== original.description ||
    status !== original.status ||
    dueDate !== original.dueDate ||
    assigneeId !== original.assigneeId;

  const handleClose = async () => {
    if (isSaving) return;

    if (hasChanges && canEdit) {
      setIsSaving(true);
      try {
        await updateTask.mutateAsync({
          taskId: task.id,
          data: {
            title,
            description: description || null,
            status,
            due_date: dueDate || null,
            assignee_id: assigneeId,
          },
        });
        setShowSaved(true);
        setTimeout(() => {
          setIsSaving(false);
          onClose();
        }, 400);
      } catch {
        setIsSaving(false);
        onClose();
      }
    } else {
      onClose();
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
      handleClose();
    }
  };

  const inputClass =
    'border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:bg-gray-100 disabled:cursor-not-allowed';

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div ref={modalRef} className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6 w-full max-w-lg">
        <div className="flex justify-between items-center mb-4">
          {!canEdit && (
            <span className="text-xs bg-yellow-200 text-black border-2 border-black font-bold px-2 py-1">
              읽기 전용
            </span>
          )}
          <div className="ml-auto">
            {isSaving && (
              <span className="text-xs font-bold text-muted-foreground">저장 중...</span>
            )}
            {showSaved && (
              <span className="text-xs font-bold text-green-700">저장됨 ✓</span>
            )}
          </div>
        </div>

        <div className="space-y-4 mb-6">
          <div>
            <label className="font-bold text-sm block mb-1">제목</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={!canEdit || isSaving}
              className={inputClass}
            />
          </div>

          <div>
            <label className="font-bold text-sm block mb-1">설명</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={!canEdit || isSaving}
              placeholder="설명 (선택)"
              className={`${inputClass} min-h-[80px] resize-none`}
            />
          </div>

          <div>
            <label className="font-bold text-sm block mb-1">상태</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as TaskStatus)}
              disabled={!canEdit || isSaving}
              className={inputClass}
            >
              {statusOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="font-bold text-sm block mb-1">마감일</label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              disabled={!canEdit || isSaving}
              className={inputClass}
            />
          </div>

          <div>
            <label className="font-bold text-sm block mb-1">담당자</label>
            <select
              value={assigneeId || ''}
              onChange={(e) => setAssigneeId(e.target.value || null)}
              disabled={!canEdit || isSaving}
              className={inputClass}
            >
              <option value="">담당자 없음</option>
              {members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {member.user.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-between">
          <div>
            {canDelete && onDelete && (
              <button
                type="button"
                disabled={isSaving}
                onClick={() => {
                  if (confirm('정말 삭제하시겠습니까?')) {
                    onDelete(task.id);
                    onClose();
                  }
                }}
                className="bg-red-500 text-white border-2 border-black font-bold px-4 py-2 text-sm hover:bg-red-600 transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50"
              >
                삭제
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={isSaving}
            className="border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-100 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
