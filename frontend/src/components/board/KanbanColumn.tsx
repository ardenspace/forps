import type { Task, TaskStatus } from '@/types/task';
import { TaskCard } from './TaskCard';

interface KanbanColumnProps {
  status: TaskStatus;
  title: string;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
}

const statusColors: Record<TaskStatus, string> = {
  todo: 'bg-slate-100',
  doing: 'bg-blue-100',
  done: 'bg-green-100',
  blocked: 'bg-red-100',
};

export function KanbanColumn({ status, title, tasks, onTaskClick }: KanbanColumnProps) {
  return (
    <div className={`flex-1 min-w-[250px] rounded-lg p-3 ${statusColors[status]}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">{title}</h3>
        <span className="text-xs text-muted-foreground bg-white px-2 py-0.5 rounded">
          {tasks.length}
        </span>
      </div>
      <div className="space-y-2">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onClick={() => onTaskClick(task)} />
        ))}
        {tasks.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-4">
            태스크 없음
          </p>
        )}
      </div>
    </div>
  );
}
