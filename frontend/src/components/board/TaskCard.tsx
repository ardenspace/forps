import { useDraggable } from '@dnd-kit/core';
import type { Task } from '@/types/task';

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
      className={`bg-white border-2 border-black shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] hover:shadow-[4px_4px_0px_0px_rgba(244,0,4,1)] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all cursor-pointer p-2.5 sm:p-3 ${
        isDragging ? 'opacity-30' : ''
      }`}
      onClick={onClick}
    >
      <h4 className="font-bold text-xs sm:text-sm break-words">{task.title}</h4>
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
    <div className="bg-white border-2 border-black shadow-[6px_6px_0px_0px_rgba(244,0,4,1)] p-2.5 sm:p-3 rotate-2 w-[220px] sm:w-[250px]">
      <h4 className="font-bold text-xs sm:text-sm break-words">{task.title}</h4>
      {task.assignee && (
        <p className="text-[11px] sm:text-xs text-muted-foreground mt-1 break-words">{task.assignee.name}</p>
      )}
    </div>
  );
}
