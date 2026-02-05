import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useUpdateTask } from '@/hooks/useTasks';
import type { Task, TaskStatus } from '@/types/task';
import type { WorkspaceRole } from '@/types/workspace';

interface TaskDetailModalProps {
  task: Task | null;
  myRole: WorkspaceRole;
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

export function TaskDetailModal({ task, myRole, isOpen, onClose, onDelete }: TaskDetailModalProps) {
  const updateTask = useUpdateTask();
  const [status, setStatus] = useState<TaskStatus>(task?.status ?? 'todo');

  useEffect(() => {
    if (task) {
      setStatus(task.status);
    }
  }, [task]);

  const canEdit = myRole === 'owner' || myRole === 'editor';
  const canDelete = myRole === 'owner';

  if (!isOpen || !task) return null;

  const handleStatusChange = async (newStatus: TaskStatus) => {
    setStatus(newStatus);
    await updateTask.mutateAsync({
      taskId: task.id,
      data: { status: newStatus },
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-lg font-bold">{task.title}</h2>
          {!canEdit && (
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
              읽기 전용
            </span>
          )}
        </div>

        {task.description && (
          <p className="text-sm text-muted-foreground mb-4">{task.description}</p>
        )}

        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium w-20">상태:</span>
            {canEdit ? (
              <select
                value={status}
                onChange={(e) => handleStatusChange(e.target.value as TaskStatus)}
                className="border rounded px-2 py-1 text-sm"
              >
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            ) : (
              <span className="text-sm">{status}</span>
            )}
          </div>
          {task.assignee && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium w-20">담당자:</span>
              <span className="text-sm">{task.assignee.name}</span>
            </div>
          )}
          {task.due_date && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium w-20">마감일:</span>
              <span className="text-sm">{new Date(task.due_date).toLocaleDateString()}</span>
            </div>
          )}
        </div>

        <div className="flex justify-between">
          <div>
            {canDelete && onDelete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={() => {
                  if (confirm('정말 삭제하시겠습니까?')) {
                    onDelete(task.id);
                    onClose();
                  }
                }}
              >
                삭제
              </Button>
            )}
          </div>
          <Button variant="ghost" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
}
