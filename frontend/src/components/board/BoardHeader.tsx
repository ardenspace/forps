import { useUIStore } from '@/stores/uiStore';

interface BoardHeaderProps {
  projectName: string;
  onCreateTask: () => void;
}

export function BoardHeader({ projectName, onCreateTask }: BoardHeaderProps) {
  const { taskFilters, setTaskFilters } = useUIStore();

  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="font-black text-xl">{projectName}</h2>
      <div className="flex items-center gap-3">
        <label className="font-medium text-sm flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={taskFilters.mineOnly}
            onChange={(e) => setTaskFilters({ mineOnly: e.target.checked })}
            className="w-4 h-4 border-2 border-black accent-yellow-400"
          />
          내 태스크만
        </label>
        <button
          onClick={onCreateTask}
          className="bg-black text-white border-2 border-black font-bold px-4 py-1.5 text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
        >
          새 태스크
        </button>
      </div>
    </div>
  );
}
