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

  const rowBg = isToday ? 'bg-brand-neon/30' : isPast ? 'bg-black/5' : 'bg-white/50';
  const borderBottom = isLast ? '' : 'border-b border-brand-blue/10';

  return (
    <div className={`flex items-stretch ${rowBg} ${borderBottom}`}>
      {/* Left label cell */}
      <div className="w-14 sm:w-20 flex-shrink-0 flex flex-col items-center justify-center p-2 sm:p-3 border-r border-brand-blue/10">
        {date ? (
          <>
            <span className={`text-[10px] sm:text-xs font-bold uppercase ${isPast ? 'text-brand-blue/50' : 'text-brand-blue/80'}`}>
              {dayOfWeek}
            </span>
            <span className={`text-xl sm:text-2xl font-black leading-none ${isPast ? 'text-brand-blue/50' : 'text-brand-blue'}`}>
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
            className={`border border-white/60 rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 cursor-pointer px-3 py-1.5 transition-all ${isToday ? 'bg-white/80' : 'glass'}`}
          >
            <p className="text-xs font-bold text-brand-blue max-w-[120px] sm:max-w-[160px] truncate">{task.title}</p>
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
