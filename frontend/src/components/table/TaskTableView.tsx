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
    <div className="border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-sm">
          <thead className="bg-yellow-100 border-b-2 border-black">
            <tr>
              <th className="text-left px-3 py-2 font-black">제목</th>
              <th className="text-left px-3 py-2 font-black">상태</th>
              <th className="text-left px-3 py-2 font-black">담당자</th>
              <th className="text-left px-3 py-2 font-black">마감일</th>
              <th className="text-left px-3 py-2 font-black">생성일</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr
                key={task.id}
                className="border-b border-black/20 hover:bg-yellow-50 cursor-pointer"
                onClick={() => onTaskClick(task)}
              >
                <td className="px-3 py-2 font-medium">{task.title}</td>
                <td className="px-3 py-2">{statusLabel[task.status] ?? task.status}</td>
                <td className="px-3 py-2">{task.assignee?.name ?? '-'}</td>
                <td className="px-3 py-2">
                  {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
                </td>
                <td className="px-3 py-2">{new Date(task.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {!tasks.length && (
              <tr>
                <td className="px-3 py-8 text-center text-muted-foreground" colSpan={5}>
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
