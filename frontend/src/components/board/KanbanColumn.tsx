import { useDroppable } from '@dnd-kit/core';
import type { Task, TaskStatus } from '@/types/task';
import { TaskCard } from './TaskCard';

interface KanbanColumnProps {
  status: TaskStatus;
  title: string;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  isDragDisabled?: boolean;
}

const statusStyles: Record<TaskStatus, string> = {
  todo: 'bg-white/30 border-white/40',
  doing: 'bg-brand-neon/10 border-brand-neon/20',
  done: 'bg-brand-sky/20 border-brand-sky/30',
  blocked: 'bg-brand-orange/10 border-brand-orange/20',
};

export function KanbanColumn({ status, title, tasks, onTaskClick, isDragDisabled }: KanbanColumnProps) {
  const { isOver, setNodeRef } = useDroppable({
    id: status,
  });

  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-w-[220px] sm:min-w-[250px] rounded-2xl border p-3 sm:p-4 backdrop-blur-sm shadow-sm transition-all duration-200 ${statusStyles[status]} ${
        isOver ? 'ring-2 ring-brand-neon bg-brand-neon/20 scale-[1.01]' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-sm uppercase tracking-wide text-brand-blue">{title}</h3>
        <span className="bg-brand-blue text-white text-[10px] px-2.5 py-1 rounded-full font-bold shadow-sm">
          {tasks.length}
        </span>
      </div>
      <div className="space-y-2">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onClick={() => onTaskClick(task)}
            isDragDisabled={isDragDisabled}
          />
        ))}
        {tasks.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-4 font-medium">
            태스크 없음
          </p>
        )}
      </div>
    </div>
  );
}
