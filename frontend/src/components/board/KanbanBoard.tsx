import type { Task, TaskStatus } from '@/types/task';
import { KanbanColumn } from './KanbanColumn';

interface KanbanBoardProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
}

const columns: { status: TaskStatus; title: string }[] = [
  { status: 'todo', title: 'To Do' },
  { status: 'doing', title: 'Doing' },
  { status: 'done', title: 'Done' },
  { status: 'blocked', title: 'Blocked' },
];

export function KanbanBoard({ tasks, onTaskClick }: KanbanBoardProps) {
  const tasksByStatus = columns.map((col) => ({
    ...col,
    tasks: tasks.filter((t) => t.status === col.status),
  }));

  return (
    <div className="flex gap-3 md:gap-4 overflow-x-auto pb-3 md:pb-4">
      {tasksByStatus.map((col) => (
        <KanbanColumn
          key={col.status}
          status={col.status}
          title={col.title}
          tasks={col.tasks}
          onTaskClick={onTaskClick}
        />
      ))}
    </div>
  );
}
