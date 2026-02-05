import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import type { SharedProjectData, SharedTask } from '@/types/share';

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  doing: 'Doing',
  done: 'Done',
  blocked: 'Blocked',
};

const statusColors: Record<string, string> = {
  todo: 'bg-slate-100',
  doing: 'bg-blue-100',
  done: 'bg-green-100',
  blocked: 'bg-red-100',
};

export function SharePage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<SharedProjectData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(`${apiUrl}/share/${token}`);
        if (!response.ok) {
          if (response.status === 404) {
            setError('공유 링크가 존재하지 않거나 만료되었습니다.');
          } else {
            setError('데이터를 불러오는 데 실패했습니다.');
          }
          return;
        }
        const result = await response.json();
        setData(result);
      } catch {
        setError('네트워크 오류가 발생했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    if (token) {
      fetchData();
    }
  }, [token]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">오류</h1>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Group tasks by status
  const tasksByStatus = ['todo', 'doing', 'done', 'blocked'].map((status) => ({
    status,
    label: statusLabels[status],
    tasks: data.tasks.filter((t) => t.status === status),
  }));

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-xl font-bold">{data.project_name}</h1>
          <p className="text-sm text-muted-foreground">공유된 프로젝트 (읽기 전용)</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="flex gap-4 overflow-x-auto pb-4">
          {tasksByStatus.map((col) => (
            <div
              key={col.status}
              className={`flex-1 min-w-[250px] rounded-lg p-3 ${statusColors[col.status]}`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-sm">{col.label}</h3>
                <span className="text-xs text-muted-foreground bg-white px-2 py-0.5 rounded">
                  {col.tasks.length}
                </span>
              </div>
              <div className="space-y-2">
                {col.tasks.map((task) => (
                  <TaskCard key={task.id} task={task} />
                ))}
                {col.tasks.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    태스크 없음
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function TaskCard({ task }: { task: SharedTask }) {
  return (
    <Card>
      <CardContent className="p-3">
        <h4 className="font-medium text-sm">{task.title}</h4>
        {task.assignee_name && (
          <p className="text-xs text-muted-foreground mt-1">{task.assignee_name}</p>
        )}
        {task.due_date && (
          <p className="text-xs text-muted-foreground">
            {new Date(task.due_date).toLocaleDateString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
