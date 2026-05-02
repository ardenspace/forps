import { useUIStore } from '@/stores/uiStore';

interface BoardHeaderProps {
  projectName: string;
  onCreateTask: () => void;
}

export function BoardHeader({ projectName, onCreateTask }: BoardHeaderProps) {
  const { taskFilters, setTaskFilters } = useUIStore();

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <h2 className="font-bold text-lg sm:text-xl break-words text-brand-blue">{projectName}</h2>
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
        <label className="font-medium text-xs sm:text-sm flex items-center gap-2 cursor-pointer text-brand-blue/80 hover:text-brand-blue transition-colors">
          <input
            type="checkbox"
            checked={taskFilters.mineOnly}
            onChange={(e) => setTaskFilters({ mineOnly: e.target.checked })}
            className="w-4 h-4 border border-brand-blue/30 rounded text-brand-blue accent-brand-blue focus:ring-brand-blue"
          />
          내 태스크만
        </label>
        <button
          onClick={onCreateTask}
          className="bg-brand-neon text-brand-coffee border border-brand-neon/50 font-bold px-4 sm:px-5 py-2 rounded-xl text-xs sm:text-sm hover:brightness-110 transition-all shadow-sm w-full sm:w-auto"
        >
          새 태스크
        </button>
      </div>
    </div>
  );
}
