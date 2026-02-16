import { useState, useRef } from 'react';
import { useCreateTask } from '@/hooks/useTasks';
import type { TaskStatus } from '@/types/task';
import type { WorkspaceMember } from '@/types/workspace';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { DatePicker } from '@/components/ui/DatePicker';

interface CreateTaskModalProps {
  projectId: string;
  members: WorkspaceMember[];
  currentUserId: string;
  isOpen: boolean;
  onClose: () => void;
}

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'todo', label: 'To Do' },
  { value: 'doing', label: 'Doing' },
  { value: 'done', label: 'Done' },
  { value: 'blocked', label: 'Blocked' },
];

export function CreateTaskModal({ projectId, members, currentUserId, isOpen, onClose }: CreateTaskModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<TaskStatus>('todo');
  const [dueDate, setDueDate] = useState('');
  const [assigneeId, setAssigneeId] = useState<string>(currentUserId);
  const createTask = useCreateTask(projectId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTask.mutateAsync({
      title,
      description: description || undefined,
      status,
      due_date: dueDate || undefined,
      assignee_id: assigneeId || undefined,
    });
    setTitle('');
    setDescription('');
    setStatus('todo');
    setDueDate('');
    setAssigneeId(currentUserId);
    onClose();
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
      onClose();
    }
  };

  if (!isOpen) return null;

  const memberOptions = [
    { value: '', label: '담당자 없음' },
    ...members.map((m) => ({
      value: m.user_id,
      label: m.user_id === currentUserId ? `${m.user.name} (나)` : m.user.name,
    })),
  ];

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div ref={modalRef} className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6 w-full max-w-md">
        <h2 className="font-black text-lg mb-4">새 태스크</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="font-bold text-sm block mb-1">제목 *</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="태스크 제목"
                required
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              />
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">설명</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="태스크 설명 (선택)"
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] min-h-[80px] resize-none"
              />
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">상태</label>
              <CustomSelect
                value={status}
                onChange={(v) => setStatus(v as TaskStatus)}
                options={statusOptions}
              />
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">담당자</label>
              <CustomSelect
                value={assigneeId}
                onChange={setAssigneeId}
                options={memberOptions}
              />
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">마감일</label>
              <DatePicker
                value={dueDate}
                onChange={setDueDate}
                placeholder="날짜 선택"
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
              disabled={createTask.isPending}
              className="bg-black text-white border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50"
            >
              {createTask.isPending ? '생성 중...' : '생성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
