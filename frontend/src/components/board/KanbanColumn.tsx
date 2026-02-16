import type { Task, TaskStatus } from '@/types/task';
import { TaskCard } from './TaskCard';

interface KanbanColumnProps {
  status: TaskStatus;
  title: string;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
}

const statusStyles: Record<TaskStatus, string> = {
  todo: 'bg-white',
  doing: 'bg-yellow-50',
  done: 'bg-green-50',
  blocked: 'bg-red-50',
};

export function KanbanColumn({ status, title, tasks, onTaskClick }: KanbanColumnProps) {
  return (
    <div
      className={`flex-1 min-w-[220px] sm:min-w-[250px] border-2 border-black p-2.5 sm:p-3 shadow-[4px_4px_0px_0px_rgba(244,0,4,1)] ${statusStyles[status]}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-black text-sm uppercase tracking-wide">{title}</h3>
        <span className="bg-black text-white text-xs px-2 py-0.5 font-bold">
          {tasks.length}
        </span>
      </div>
      <div className="space-y-2">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onClick={() => onTaskClick(task)} />
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
