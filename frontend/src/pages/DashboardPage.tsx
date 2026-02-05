import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useWorkspaces } from '@/hooks/useWorkspaces';
import { useProjects } from '@/hooks/useProjects';
import { useTasks, useDeleteTask } from '@/hooks/useTasks';
import { useUIStore } from '@/stores/uiStore';
import { Button } from '@/components/ui/button';
import { KanbanBoard } from '@/components/board/KanbanBoard';
import { BoardHeader } from '@/components/board/BoardHeader';
import { CreateTaskModal } from '@/components/board/CreateTaskModal';
import { TaskDetailModal } from '@/components/board/TaskDetailModal';
import type { Task } from '@/types/task';

export function DashboardPage() {
  const { user, logout } = useAuth();
  const {
    selectedWorkspaceId,
    selectedProjectId,
    setSelectedWorkspace,
    setSelectedProject,
    taskFilters,
  } = useUIStore();

  const { data: workspaces } = useWorkspaces();
  const { data: projects } = useProjects(selectedWorkspaceId);
  const { data: tasks, isLoading } = useTasks(selectedProjectId, {
    mine_only: taskFilters.mineOnly,
  });
  const deleteTaskMutation = useDeleteTask();

  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const selectedProject = projects?.find((p) => p.id === selectedProjectId);
  const myRole = selectedProject?.my_role ?? 'viewer';

  const handleDeleteTask = (taskId: string) => {
    deleteTaskMutation.mutate(taskId);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">for-ps</h1>
            {/* Workspace selector */}
            <select
              value={selectedWorkspaceId || ''}
              onChange={(e) => setSelectedWorkspace(e.target.value || null)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="">워크스페이스 선택</option>
              {workspaces?.map((ws) => (
                <option key={ws.id} value={ws.id}>{ws.name}</option>
              ))}
            </select>
            {/* Project selector */}
            {selectedWorkspaceId && (
              <select
                value={selectedProjectId || ''}
                onChange={(e) => setSelectedProject(e.target.value || null)}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="">프로젝트 선택</option>
                {projects?.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{user?.name}</span>
            <Button variant="ghost" size="sm" onClick={logout}>
              로그아웃
            </Button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto px-4 py-6">
        {!selectedProjectId ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              워크스페이스와 프로젝트를 선택해주세요.
            </p>
          </div>
        ) : isLoading ? (
          <div className="text-center py-12">로딩 중...</div>
        ) : (
          <>
            <BoardHeader
              projectName={selectedProject?.name || ''}
              onCreateTask={() => setCreateModalOpen(true)}
            />
            <KanbanBoard
              tasks={tasks || []}
              onTaskClick={(task) => setSelectedTask(task)}
            />
          </>
        )}
      </main>

      {/* Modals */}
      {selectedProjectId && (
        <CreateTaskModal
          projectId={selectedProjectId}
          isOpen={isCreateModalOpen}
          onClose={() => setCreateModalOpen(false)}
        />
      )}

      <TaskDetailModal
        task={selectedTask}
        myRole={myRole}
        isOpen={!!selectedTask}
        onClose={() => setSelectedTask(null)}
        onDelete={handleDeleteTask}
      />
    </div>
  );
}
