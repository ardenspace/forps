import { Card, CardContent } from '@/components/ui/card';
import type { Task } from '@/types/task';

interface TaskCardProps {
  task: Task;
  onClick: () => void;
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardContent className="p-3">
        <h4 className="font-medium text-sm">{task.title}</h4>
        {task.assignee && (
          <p className="text-xs text-muted-foreground mt-1">
            {task.assignee.name}
          </p>
        )}
        {task.due_date && (
          <p className="text-xs text-muted-foreground">
            {new Date(task.due_date).toLocaleDateString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
