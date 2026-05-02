import type { Task } from '@/types/task';

interface TaskTableViewProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
}

const statusLabel: Record<string, string> = {
  todo: 'To Do',
  doing: 'Doing',
  done: 'Done',
  blocked: 'Blocked',
};

export function TaskTableView({ tasks, onTaskClick }: TaskTableViewProps) {
  return (
    <div className="glass-panel rounded-2xl overflow-hidden shadow-md">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] sm:min-w-[760px] text-xs sm:text-sm">
          <thead className="bg-brand-blue/5 border-b border-white/40">
            <tr>
              <th className="text-left px-2.5 sm:px-4 py-3 font-bold text-brand-blue/80 uppercase tracking-wider">제목</th>
              <th className="text-left px-2.5 sm:px-4 py-3 font-bold text-brand-blue/80 uppercase tracking-wider">상태</th>
              <th className="text-left px-2.5 sm:px-4 py-3 font-bold text-brand-blue/80 uppercase tracking-wider">담당자</th>
              <th className="text-left px-2.5 sm:px-4 py-3 font-bold text-brand-blue/80 uppercase tracking-wider">마감일</th>
              <th className="text-left px-2.5 sm:px-4 py-3 font-bold text-brand-blue/80 uppercase tracking-wider">생성일</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr
                key={task.id}
                className="border-b border-white/40 hover:bg-white/60 cursor-pointer transition-colors text-brand-blue"
                onClick={() => onTaskClick(task)}
              >
                <td className="px-2.5 sm:px-4 py-3 font-bold max-w-[240px] truncate">{task.title}</td>
                <td className="px-2.5 sm:px-4 py-3">{statusLabel[task.status] ?? task.status}</td>
                <td className="px-2.5 sm:px-4 py-3">{task.assignee?.name ?? '-'}</td>
                <td className="px-2.5 sm:px-4 py-3">
                  {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
                </td>
                <td className="px-2.5 sm:px-4 py-3">{new Date(task.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {!tasks.length && (
              <tr>
                <td className="px-2.5 sm:px-3 py-8 text-center text-muted-foreground" colSpan={5}>
                  표시할 태스크가 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
