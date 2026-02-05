import { Card, CardContent } from '@/components/ui/card';
import type { Task } from '@/types/task';

interface WeekColumnProps {
  date: Date | null;
  label: string;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  isToday?: boolean;
}

export function WeekColumn({ date, label, tasks, onTaskClick, isToday }: WeekColumnProps) {
  const dayOfWeek = date ? date.toLocaleDateString('ko-KR', { weekday: 'short' }) : '';
  const dayOfMonth = date ? date.getDate() : '';

  return (
    <div className={`flex-1 min-w-[150px] rounded-lg p-3 ${isToday ? 'bg-blue-50' : 'bg-gray-50'}`}>
      <div className="text-center mb-3">
        {date ? (
          <>
            <p className="text-xs text-muted-foreground">{dayOfWeek}</p>
            <p className={`text-lg font-bold ${isToday ? 'text-blue-600' : ''}`}>{dayOfMonth}</p>
          </>
        ) : (
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
        )}
        <span className="text-xs text-muted-foreground bg-white px-2 py-0.5 rounded">
          {tasks.length}
        </span>
      </div>
      <div className="space-y-2">
        {tasks.map((task) => (
          <Card
            key={task.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onTaskClick(task)}
          >
            <CardContent className="p-2">
              <p className="text-xs font-medium truncate">{task.title}</p>
              {task.assignee && (
                <p className="text-xs text-muted-foreground truncate">{task.assignee.name}</p>
              )}
            </CardContent>
          </Card>
        ))}
        {tasks.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-2">없음</p>
        )}
      </div>
    </div>
  );
}
