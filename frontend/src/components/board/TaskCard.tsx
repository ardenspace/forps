import { useDraggable } from '@dnd-kit/core';
import { TASK_SOURCE, type Task } from '@/types/task';

interface TaskCardProps {
  task: Task;
  onClick: () => void;
  isDragDisabled?: boolean;
}

export function TaskCard({ task, onClick, isDragDisabled = false }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id,
    data: { task },
    disabled: isDragDisabled,
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={`glass border border-white/60 hover:bg-white/60 transition-all duration-200 rounded-xl cursor-pointer p-3 sm:p-4 ${
        isDragging ? 'opacity-40 scale-105 shadow-xl rotate-2' : 'shadow-sm hover:shadow-md hover:-translate-y-0.5'
      }`}
      onClick={onClick}
    >
      <h4 className="font-bold text-xs sm:text-sm text-brand-blue break-words">
        {task.title}
        {task.source === TASK_SOURCE.SYNCED_FROM_PLAN && (
          <span
            className="ml-1 rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700"
            title="PLAN.md 에서 자동 동기화된 태스크"
          >
            PLAN
          </span>
        )}
        {task.handoff_missing && (
          <span
            className="ml-1 rounded bg-white/60 px-1.5 py-0.5 text-[10px] font-medium text-yellow-800"
            title="이 commit 의 handoff 기록이 없습니다 — 작업 기록 빠짐"
          >
            ⚠️ 기록 빠짐
          </span>
        )}
      </h4>
      {task.assignee && (
        <p className="text-[11px] sm:text-xs text-muted-foreground mt-1 break-words">{task.assignee.name}</p>
      )}
      {task.due_date && (
        <p className="text-[11px] sm:text-xs text-muted-foreground">
          {new Date(task.due_date).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}

/** Overlay version (no drag hooks, just visual) */
export function TaskCardOverlay({ task }: { task: Task }) {
  return (
    <div className="glass border border-white/80 shadow-xl rounded-xl p-3 sm:p-4 rotate-3 w-[220px] sm:w-[250px] scale-105 z-50">
      <h4 className="font-bold text-xs sm:text-sm text-brand-blue break-words">{task.title}</h4>
      {task.assignee && (
        <p className="text-[11px] sm:text-xs text-brand-blue/60 mt-1 break-words">{task.assignee.name}</p>
      )}
    </div>
  );
}
