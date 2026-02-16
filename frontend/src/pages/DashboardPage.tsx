import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useWorkspaces, useWorkspaceMembers } from '@/hooks/useWorkspaces';
import { useProjects } from '@/hooks/useProjects';
import { useTasks, useDeleteTask, useWeekTasks } from '@/hooks/useTasks';
import { useUIStore } from '@/stores/uiStore';
import { Button } from '@/components/ui/button';
import { KanbanBoard } from '@/components/board/KanbanBoard';
import { BoardHeader } from '@/components/board/BoardHeader';
import { CreateTaskModal } from '@/components/board/CreateTaskModal';
import { TaskDetailModal } from '@/components/board/TaskDetailModal';
import { CreateProjectModal } from '@/components/workspace/CreateProjectModal';
import { WeekView, getMonday } from '@/components/week/WeekView';
import type { Task } from '@/types/task';

type ViewMode = 'board' | 'week';

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

  useEffect(() => {
    if (workspaces && workspaces.length > 0 && !selectedWorkspaceId) {
      setSelectedWorkspace(workspaces[0].id);
    }
  }, [workspaces, selectedWorkspaceId, setSelectedWorkspace]);

  const currentWorkspace = workspaces?.find((ws) => ws.id === selectedWorkspaceId);

  const { data: projects } = useProjects(selectedWorkspaceId);
  const { data: members } = useWorkspaceMembers(selectedWorkspaceId);
  const { data: tasks, isLoading } = useTasks(selectedProjectId, {
    mine_only: taskFilters.mineOnly,
  });
  const deleteTaskMutation = useDeleteTask();

  const [viewMode, setViewMode] = useState<ViewMode>('board');
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const [isCreateTaskModalOpen, setCreateTaskModalOpen] = useState(false);
  const [isCreateProjectModalOpen, setCreateProjectModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const weekStartStr = weekStart.toISOString().split('T')[0];
  const { data: weekTasks, isLoading: isWeekLoading } = useWeekTasks(
    viewMode === 'week' ? weekStartStr : null
  );

  const selectedProject = projects?.find((p) => p.id === selectedProjectId);
  const myRole = selectedProject?.my_role ?? 'viewer';

  const handleDeleteTask = (taskId: string) => {
    deleteTaskMutation.mutate(taskId);
  };

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b-2 border-black bg-card flex-shrink-0 shadow-[0px_2px_0px_0px_rgba(0,0,0,1)]">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-black tracking-tight">forps</h1>
            {/* View Mode Tabs */}
            <div className="flex border-2 border-black rounded overflow-hidden shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
              <button
                className={`px-3 py-1 text-sm font-bold transition-colors ${
                  viewMode === 'board'
                    ? 'bg-black text-white'
                    : 'bg-background hover:bg-yellow-100'
                }`}
                onClick={() => setViewMode('board')}
              >
                Board
              </button>
              <button
                className={`px-3 py-1 text-sm font-bold border-l-2 border-black transition-colors ${
                  viewMode === 'week'
                    ? 'bg-black text-white'
                    : 'bg-background hover:bg-yellow-100'
                }`}
                onClick={() => setViewMode('week')}
              >
                Week
              </button>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">{user?.name}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="border-2 border-black font-bold hover:bg-yellow-400 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all"
            >
              로그아웃
            </Button>
          </div>
        </div>
      </header>

      {/* Body: Sidebar + Main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-56 border-r-2 border-black bg-card flex-shrink-0 flex flex-col p-4">
          {/* Workspace name */}
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 truncate">
            {currentWorkspace?.name ?? '워크스페이스'}
          </p>

          <div className="flex flex-col flex-1 overflow-hidden">
            {/* Section label */}
            <p className="text-xs text-muted-foreground mb-1 font-medium">프로젝트</p>

            {/* Project list */}
            <ul className="flex flex-col gap-0.5 overflow-y-auto flex-1">
              {projects?.map((project) => {
                const isSelected = project.id === selectedProjectId;
                return (
                  <li key={project.id}>
                    <button
                      className={`w-full text-left px-2 py-1.5 rounded text-sm font-medium transition-all border-2 ${
                        isSelected
                          ? 'bg-yellow-400 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] font-bold'
                          : 'border-transparent text-muted-foreground hover:bg-yellow-50 hover:border-black hover:text-foreground'
                      }`}
                      onClick={() => setSelectedProject(project.id)}
                    >
                      <span className="truncate block">{project.name}</span>
                    </button>
                  </li>
                );
              })}
              {!projects?.length && (
                <li>
                  <p className="text-xs text-muted-foreground px-2 py-1.5 italic">
                    프로젝트 없음
                  </p>
                </li>
              )}
            </ul>
          </div>

          {/* New project button */}
          {selectedWorkspaceId && (
            <button
              className="mt-4 text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 px-2 py-1.5 rounded border-2 border-dashed border-muted-foreground hover:border-black hover:bg-yellow-50 transition-all font-medium w-full"
              onClick={() => setCreateProjectModalOpen(true)}
            >
              <span className="text-base leading-none">+</span>
              <span>새 프로젝트</span>
            </button>
          )}
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          {viewMode === 'board' ? (
            !selectedProjectId ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center border-2 border-black shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] bg-white p-10 rounded">
                  <p className="text-muted-foreground font-medium text-base">
                    ← 왼쪽에서 프로젝트를 선택하세요.
                  </p>
                </div>
              </div>
            ) : isLoading ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-muted-foreground font-medium">로딩 중...</p>
              </div>
            ) : (
              <>
                <BoardHeader
                  projectName={selectedProject?.name || ''}
                  onCreateTask={() => setCreateTaskModalOpen(true)}
                />
                <KanbanBoard
                  tasks={tasks || []}
                  onTaskClick={(task) => setSelectedTask(task)}
                />
              </>
            )
          ) : isWeekLoading ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-muted-foreground font-medium">로딩 중...</p>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-black mb-4">내 주간 태스크</h2>
              <WeekView
                tasks={weekTasks || []}
                weekStart={weekStart}
                onWeekChange={setWeekStart}
                onTaskClick={(task) => setSelectedTask(task)}
              />
            </>
          )}
        </main>
      </div>

      {/* Modals */}
      {selectedProjectId && viewMode === 'board' && user && (
        <CreateTaskModal
          projectId={selectedProjectId}
          members={members || []}
          currentUserId={user.id}
          isOpen={isCreateTaskModalOpen}
          onClose={() => setCreateTaskModalOpen(false)}
        />
      )}

      {selectedWorkspaceId && (
        <CreateProjectModal
          workspaceId={selectedWorkspaceId}
          isOpen={isCreateProjectModalOpen}
          onClose={() => setCreateProjectModalOpen(false)}
        />
      )}

      <TaskDetailModal
        task={selectedTask}
        myRole={myRole}
        members={members || []}
        isOpen={!!selectedTask}
        onClose={() => setSelectedTask(null)}
        onDelete={handleDeleteTask}
      />
    </div>
  );
}
