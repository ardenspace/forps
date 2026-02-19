import { useState } from 'react';
import { DndContext, DragOverlay, PointerSensor, TouchSensor, useSensor, useSensors } from '@dnd-kit/core';
import type { DragStartEvent, DragEndEvent } from '@dnd-kit/core';
import type { Task, TaskStatus } from '@/types/task';
import { KanbanColumn } from './KanbanColumn';
import { TaskCardOverlay } from './TaskCard';

interface KanbanBoardProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  onTaskStatusChange?: (taskId: string, newStatus: TaskStatus) => void;
  isDragDisabled?: boolean;
}

const columns: { status: TaskStatus; title: string }[] = [
  { status: 'todo', title: 'To Do' },
  { status: 'doing', title: 'Doing' },
  { status: 'done', title: 'Done' },
  { status: 'blocked', title: 'Blocked' },
];

const VALID_STATUSES = new Set<string>(columns.map((c) => c.status));

export function KanbanBoard({ tasks, onTaskClick, onTaskStatusChange, isDragDisabled }: KanbanBoardProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const pointerSensor = useSensor(PointerSensor, {
    activationConstraint: { distance: 5 },
  });
  const touchSensor = useSensor(TouchSensor, {
    activationConstraint: { delay: 200, tolerance: 5 },
  });
  const sensors = useSensors(pointerSensor, touchSensor);

  const tasksByStatus = columns.map((col) => ({
    ...col,
    tasks: tasks.filter((t) => t.status === col.status),
  }));

  const handleDragStart = (event: DragStartEvent) => {
    const task = (event.active.data.current as { task: Task } | undefined)?.task ?? null;
    setActiveTask(task);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null);

    const { active, over } = event;
    if (!over || !onTaskStatusChange) return;

    const taskId = active.id as string;
    const newStatus = over.id as string;

    if (!VALID_STATUSES.has(newStatus)) return;

    // Find the task to check if status actually changed
    const task = tasks.find((t) => t.id === taskId);
    if (!task || task.status === newStatus) return;

    onTaskStatusChange(taskId, newStatus as TaskStatus);
  };

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex gap-3 md:gap-4 overflow-x-auto pb-3 md:pb-4">
        {tasksByStatus.map((col) => (
          <KanbanColumn
            key={col.status}
            status={col.status}
            title={col.title}
            tasks={col.tasks}
            onTaskClick={onTaskClick}
            isDragDisabled={isDragDisabled}
          />
        ))}
      </div>
      <DragOverlay>
        {activeTask ? <TaskCardOverlay task={activeTask} /> : null}
      </DragOverlay>
    </DndContext>
  );
}
