import { useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { WeekColumn } from './WeekColumn';
import type { Task } from '@/types/task';

interface WeekViewProps {
  tasks: Task[];
  weekStart: Date;
  onWeekChange: (newStart: Date) => void;
  onTaskClick: (task: Task) => void;
}

function getWeekDates(start: Date): Date[] {
  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    dates.push(date);
  }
  return dates;
}

function isSameDay(d1: Date, d2: Date): boolean {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

function getMonday(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function WeekView({ tasks, weekStart, onWeekChange, onTaskClick }: WeekViewProps) {
  const today = new Date();
  const weekDates = useMemo(() => getWeekDates(weekStart), [weekStart]);

  const tasksByDate = useMemo(() => {
    const map = new Map<string, Task[]>();

    // Initialize each day of the week
    weekDates.forEach((date) => {
      map.set(date.toISOString().split('T')[0], []);
    });
    map.set('no-date', []);

    // Group tasks
    tasks.forEach((task) => {
      if (!task.due_date) {
        const list = map.get('no-date') || [];
        list.push(task);
        map.set('no-date', list);
      } else {
        const taskDate = new Date(task.due_date);
        const key = taskDate.toISOString().split('T')[0];
        if (map.has(key)) {
          const list = map.get(key) || [];
          list.push(task);
          map.set(key, list);
        }
      }
    });

    return map;
  }, [tasks, weekDates]);

  const handlePrevWeek = () => {
    const newStart = new Date(weekStart);
    newStart.setDate(weekStart.getDate() - 7);
    onWeekChange(newStart);
  };

  const handleNextWeek = () => {
    const newStart = new Date(weekStart);
    newStart.setDate(weekStart.getDate() + 7);
    onWeekChange(newStart);
  };

  const handleThisWeek = () => {
    onWeekChange(getMonday(new Date()));
  };

  const weekEndDate = new Date(weekStart);
  weekEndDate.setDate(weekStart.getDate() + 6);

  return (
    <div>
      {/* Week Navigation */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handlePrevWeek}>
            ← 이전
          </Button>
          <Button variant="outline" size="sm" onClick={handleThisWeek}>
            이번 주
          </Button>
          <Button variant="outline" size="sm" onClick={handleNextWeek}>
            다음 →
          </Button>
        </div>
        <h3 className="text-lg font-semibold">
          {weekStart.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })} -{' '}
          {weekEndDate.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })}
        </h3>
      </div>

      {/* Week Grid */}
      <div className="flex gap-2 overflow-x-auto pb-4">
        {weekDates.map((date) => {
          const key = date.toISOString().split('T')[0];
          return (
            <WeekColumn
              key={key}
              date={date}
              label=""
              tasks={tasksByDate.get(key) || []}
              onTaskClick={onTaskClick}
              isToday={isSameDay(date, today)}
            />
          );
        })}
        <WeekColumn
          date={null}
          label="마감일 없음"
          tasks={tasksByDate.get('no-date') || []}
          onTaskClick={onTaskClick}
        />
      </div>
    </div>
  );
}

export { getMonday };
