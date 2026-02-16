import type { Task } from '@/types/task';

interface WeekRowProps {
  date: Date | null;
  label?: string;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  isToday: boolean;
  isPast: boolean;
  isLast: boolean;
}

export function WeekRow({ date, label, tasks, onTaskClick, isToday, isPast, isLast }: WeekRowProps) {
  const dayOfWeek = date ? date.toLocaleDateString('ko-KR', { weekday: 'short' }) : '';
  const dayOfMonth = date ? date.getDate() : null;

  const rowBg = isToday ? 'bg-yellow-400' : isPast ? 'bg-gray-50' : 'bg-white';
  const borderBottom = isLast ? '' : 'border-b-2 border-black';

  return (
    <div className={`flex items-stretch ${rowBg} ${borderBottom}`}>
      {/* Left label cell */}
      <div className="w-14 sm:w-20 flex-shrink-0 flex flex-col items-center justify-center p-2 sm:p-3 border-r-2 border-black">
        {date ? (
          <>
            <span className={`text-[10px] sm:text-xs font-bold uppercase ${isPast ? 'text-muted-foreground' : ''}`}>
              {dayOfWeek}
            </span>
            <span className={`text-xl sm:text-2xl font-black leading-none ${isPast ? 'text-muted-foreground' : ''}`}>
              {dayOfMonth}
            </span>
          </>
        ) : (
          <span className="text-[10px] sm:text-xs font-bold text-center leading-tight">{label}</span>
        )}
      </div>

      {/* Right task area */}
      <div className="flex-1 flex flex-wrap gap-1.5 sm:gap-2 p-2.5 sm:p-3 min-h-[56px] sm:min-h-[64px] items-start content-start">
        {tasks.map((task) => (
          <div
            key={task.id}
            onClick={() => onTaskClick(task)}
            className={`border-2 border-black shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] hover:shadow-[3px_3px_0px_0px_rgba(244,0,4,1)] hover:-translate-y-0.5 cursor-pointer px-3 py-1.5 transition-all ${isToday ? 'bg-yellow-200' : 'bg-white'}`}
          >
            <p className="text-xs font-bold max-w-[120px] sm:max-w-[160px] truncate">{task.title}</p>
            {task.assignee && (
              <p className="text-[11px] sm:text-xs text-muted-foreground truncate max-w-[120px] sm:max-w-[160px]">
                {task.assignee.name}
              </p>
            )}
          </div>
        ))}
        {tasks.length === 0 && (
          <span className="text-xs text-muted-foreground font-medium self-center">—</span>
        )}
      </div>
    </div>
  );
}
