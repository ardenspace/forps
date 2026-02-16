import type { Task } from '@/types/task';

interface TaskCardProps {
  task: Task;
  onClick: () => void;
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  return (
    <div
      className="bg-white border-2 border-black shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] hover:shadow-[4px_4px_0px_0px_rgba(244,0,4,1)] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all cursor-pointer p-2.5 sm:p-3"
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
