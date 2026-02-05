import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/uiStore';

interface BoardHeaderProps {
  projectName: string;
  onCreateTask: () => void;
}

export function BoardHeader({ projectName, onCreateTask }: BoardHeaderProps) {
  const { taskFilters, setTaskFilters } = useUIStore();

  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-xl font-bold">{projectName}</h2>
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={taskFilters.mineOnly}
            onChange={(e) => setTaskFilters({ mineOnly: e.target.checked })}
            className="rounded"
          />
          내 태스크만
        </label>
        <Button onClick={onCreateTask}>새 태스크</Button>
      </div>
    </div>
  );
}
