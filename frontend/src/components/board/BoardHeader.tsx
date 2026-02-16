import { useUIStore } from '@/stores/uiStore';

interface BoardHeaderProps {
  projectName: string;
  onCreateTask: () => void;
}

export function BoardHeader({ projectName, onCreateTask }: BoardHeaderProps) {
  const { taskFilters, setTaskFilters } = useUIStore();

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
      <h2 className="font-black text-lg sm:text-xl break-words">{projectName}</h2>
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
        <label className="font-medium text-xs sm:text-sm flex items-center gap-2 cursor-pointer">
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
          className="bg-black text-white border-2 border-black font-bold px-3 sm:px-4 py-1.5 text-xs sm:text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] w-full sm:w-auto"
        >
          새 태스크
        </button>
      </div>
    </div>
  );
}
