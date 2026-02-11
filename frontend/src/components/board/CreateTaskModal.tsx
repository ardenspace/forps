import { useState, useRef } from 'react';
import { useCreateTask } from '@/hooks/useTasks';
import type { TaskStatus } from '@/types/task';
import type { WorkspaceMember } from '@/types/workspace';

interface CreateTaskModalProps {
  projectId: string;
  members: WorkspaceMember[];
  currentUserId: string;
  isOpen: boolean;
  onClose: () => void;
}

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
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as TaskStatus)}
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              >
                <option value="todo">To Do</option>
                <option value="doing">Doing</option>
                <option value="done">Done</option>
                <option value="blocked">Blocked</option>
              </select>
            </div>
            <div>
              <label className="font-bold text-sm block mb-1">담당자</label>
              <select
                value={assigneeId}
                onChange={(e) => setAssigneeId(e.target.value)}
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              >
                <option value="">담당자 없음</option>
                {members.map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.user.name} {member.user_id === currentUserId ? '(나)' : ''}
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
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
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
