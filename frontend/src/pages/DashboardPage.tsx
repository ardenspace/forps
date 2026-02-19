import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useWorkspaces } from '@/hooks/useWorkspaces';
import { useProjects, useProjectMembers } from '@/hooks/useProjects';
import { useTasks, useDeleteTask, useUpdateTask, useWeekTasks } from '@/hooks/useTasks';
import { useSendDiscordSummary } from '@/hooks/useDiscord';
import { useUIStore } from '@/stores/uiStore';
import { Button } from '@/components/ui/button';
import { KanbanBoard } from '@/components/board/KanbanBoard';
import { BoardHeader } from '@/components/board/BoardHeader';
import { TaskModal } from '@/components/board/TaskModal';
import { CreateProjectModal } from '@/components/workspace/CreateProjectModal';
import { ProjectItem } from '@/components/sidebar/ProjectItem';
import { ProjectMemberManager } from '@/components/project/ProjectMemberManager';
import { WeekView, getMonday } from '@/components/week/WeekView';
import { TaskTableView } from '@/components/table/TaskTableView';
import { ShareLinkManager } from '@/components/share/ShareLinkManager';
import type { Task } from '@/types/task';

type ViewMode = 'board' | 'table' | 'week';

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
    if (!workspaces) {
      return;
    }

    if (workspaces.length === 0) {
      setSelectedWorkspace(null);
      return;
    }

    const hasSelectedWorkspace = selectedWorkspaceId
      ? workspaces.some((ws) => ws.id === selectedWorkspaceId)
      : false;

    if (!hasSelectedWorkspace) {
      setSelectedWorkspace(workspaces[0].id);
    }
  }, [workspaces, selectedWorkspaceId, setSelectedWorkspace]);

  const currentWorkspace = workspaces?.find((ws) => ws.id === selectedWorkspaceId);

  const { data: projects } = useProjects(selectedWorkspaceId);
  const { data: members } = useProjectMembers(selectedProjectId);
  const { data: tasks, isLoading } = useTasks(selectedProjectId, {
    mine_only: taskFilters.mineOnly,
  });
  const deleteTaskMutation = useDeleteTask();
  const updateTaskMutation = useUpdateTask();
  const discordMutation = useSendDiscordSummary(selectedWorkspaceId);

  const [viewMode, setViewMode] = useState<ViewMode>('board');
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const [isCreateTaskModalOpen, setCreateTaskModalOpen] = useState(false);
  const [isCreateProjectModalOpen, setCreateProjectModalOpen] = useState(false);
  const [isProjectMemberModalOpen, setProjectMemberModalOpen] = useState(false);
  const [isShareManagerOpen, setShareManagerOpen] = useState(false);
  const [isMobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const weekStartStr = weekStart.toISOString().split('T')[0];
  const { data: weekTasks, isLoading: isWeekLoading } = useWeekTasks(
    viewMode === 'week' ? weekStartStr : null
  );

  const selectedProject = projects?.find((p) => p.id === selectedProjectId);
  const myRole = selectedProject?.my_role ?? 'viewer';

  useEffect(() => {
    if (!projects) {
      return;
    }

    if (projects.length === 0) {
      setSelectedProject(null);
      return;
    }

    const hasSelectedProject = selectedProjectId
      ? projects.some((project) => project.id === selectedProjectId)
      : false;

    if (!hasSelectedProject) {
      setSelectedProject(projects[0].id);
    }
  }, [projects, selectedProjectId, setSelectedProject]);

  const handleDeleteTask = (taskId: string) => {
    deleteTaskMutation.mutate(taskId);
  };

  useEffect(() => {
    const mediaQuery = window.matchMedia('(min-width: 768px)');
    const handleChange = (event: MediaQueryListEvent) => {
      if (event.matches) {
        setMobileSidebarOpen(false);
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  const closeMobileSidebar = () => {
    setMobileSidebarOpen(false);
  };

  const handleProjectSelect = (projectId: string) => {
    setSelectedProject(projectId);
    closeMobileSidebar();
  };

  const sidebarContent = (
    <>
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 truncate">
        {currentWorkspace?.name ?? '워크스페이스'}
      </p>

      <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
        <p className="text-xs text-muted-foreground mb-1 font-medium">프로젝트</p>

        <ul className="flex flex-col gap-1 overflow-y-auto overflow-x-hidden pb-1 flex-1 min-h-0">
          {projects?.map((project) => (
            <ProjectItem
              key={project.id}
              project={project}
              isSelected={project.id === selectedProjectId}
              workspaceId={selectedWorkspaceId!}
              onSelect={handleProjectSelect}
            />
          ))}
          {!projects?.length && (
            <li>
              <p className="text-xs text-muted-foreground px-2 py-1.5 italic">프로젝트 없음</p>
            </li>
          )}
        </ul>
      </div>

      <div className="mt-auto pt-3 space-y-2 border-t-2 border-black/10">
        {selectedWorkspaceId && (
          <button
            className="text-xs sm:text-sm text-muted-foreground hover:text-foreground flex items-center justify-center gap-1 px-2 py-1.5 rounded border-2 border-dashed border-muted-foreground hover:border-black hover:bg-yellow-50 transition-all font-medium w-full md:w-full"
            onClick={() => {
              setCreateProjectModalOpen(true);
              closeMobileSidebar();
            }}
          >
            <span className="text-base leading-none">+</span>
            <span>새 프로젝트</span>
          </button>
        )}

        {selectedProjectId && myRole === 'owner' && (
          <button
            className="text-xs sm:text-sm text-muted-foreground hover:text-foreground flex items-center justify-center gap-1 px-2 py-1.5 rounded border-2 border-dashed border-muted-foreground hover:border-black hover:bg-yellow-50 transition-all font-medium w-full md:w-full"
            onClick={() => {
              setProjectMemberModalOpen(true);
              closeMobileSidebar();
            }}
          >
            <span>프로젝트 멤버</span>
          </button>
        )}

        {currentWorkspace?.my_role === 'owner' && (
          <button
            className="text-xs sm:text-sm text-muted-foreground hover:text-foreground flex items-center justify-center gap-1 px-2 py-1.5 rounded border-2 border-dashed border-muted-foreground hover:border-black hover:bg-purple-50 transition-all font-medium w-full md:w-full"
            disabled={discordMutation.isPending}
            onClick={() => {
              discordMutation.mutate(undefined, {
                onSuccess: () => alert('Discord 리포트가 전송되었습니다.'),
                onError: (err) => {
                  const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
                    ?? 'Discord 리포트 전송에 실패했습니다.';
                  alert(message);
                },
              });
              closeMobileSidebar();
            }}
          >
            <span>{discordMutation.isPending ? '전송 중...' : 'Discord 리포트'}</span>
          </button>
        )}
      </div>
    </>
  );

  return (
    <div className="min-h-screen md:h-screen flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="border-b-2 border-black bg-card flex-shrink-0 shadow-[0px_2px_0px_0px_rgba(244,0,4,1)]">
        <div className="px-3 py-3 sm:px-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
              <h1 className="text-lg sm:text-xl font-black tracking-tight">forps</h1>
              <div className="flex w-full sm:w-auto border-2 border-black rounded overflow-hidden shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]">
                <button
                  className={`flex-1 sm:flex-none px-2 sm:px-3 py-1.5 text-[11px] sm:text-sm font-bold transition-colors ${
                    viewMode === 'board'
                      ? 'bg-black text-white'
                      : 'bg-background hover:bg-yellow-100'
                  }`}
                  onClick={() => setViewMode('board')}
                >
                  Board
                </button>
                <button
                  className={`flex-1 sm:flex-none px-2 sm:px-3 py-1.5 text-[11px] sm:text-sm font-bold border-l-2 border-black transition-colors ${
                    viewMode === 'table'
                      ? 'bg-black text-white'
                      : 'bg-background hover:bg-yellow-100'
                  }`}
                  onClick={() => setViewMode('table')}
                >
                  Table
                </button>
                <button
                  className={`flex-1 sm:flex-none px-2 sm:px-3 py-1.5 text-[11px] sm:text-sm font-bold border-l-2 border-black transition-colors ${
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
            <div className="flex items-center justify-between gap-3 sm:justify-end">
              <button
                type="button"
                onClick={() => setMobileSidebarOpen((prev) => !prev)}
                className="md:hidden border-2 border-black font-bold text-xs px-2.5 py-1.5 bg-white hover:bg-yellow-100"
              >
                메뉴
              </button>
              <span className="text-xs sm:text-sm font-medium text-muted-foreground truncate max-w-[110px] sm:max-w-none">
                {user?.name}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="border-2 border-black font-bold text-[11px] sm:text-sm px-2.5 sm:px-3 hover:bg-yellow-400 hover:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] transition-all"
              >
                로그아웃
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Body: Sidebar + Main */}
      <div className="relative flex flex-1 min-h-0 overflow-hidden">
        <aside className="hidden md:flex w-56 border-r-2 border-black bg-card flex-shrink-0 flex-col p-4 min-h-0">
          {sidebarContent}
        </aside>

        <div
          className={`fixed inset-0 z-40 md:hidden transition ${
            isMobileSidebarOpen ? 'pointer-events-auto' : 'pointer-events-none'
          }`}
        >
          <button
            type="button"
            aria-label="사이드바 닫기"
            onClick={closeMobileSidebar}
            className={`absolute inset-0 bg-black/50 transition-opacity ${
              isMobileSidebarOpen ? 'opacity-100' : 'opacity-0'
            }`}
          />
          <aside
            className={`absolute left-0 top-0 h-full w-[82vw] max-w-xs border-r-2 border-black bg-card p-3 flex flex-col min-h-0 transition-transform duration-200 ${
              isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
            }`}
          >
            {sidebarContent}
          </aside>
        </div>

        {/* Main content */}
        <main className="flex-1 min-h-0 overflow-auto p-2.5 sm:p-4 md:p-6">
          {viewMode === 'board' || viewMode === 'table' ? (
            !selectedProjectId ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center border-2 border-black shadow-[6px_6px_0px_0px_rgba(244,0,4,1)] bg-white p-6 sm:p-10 rounded">
                  <p className="text-muted-foreground font-medium text-sm sm:text-base">
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
                {myRole === 'owner' && (
                  <div className="mb-4">
                    <Button
                      type="button"
                      className="border-2 border-black font-bold text-xs sm:text-sm w-full sm:w-auto"
                      onClick={() => setShareManagerOpen(true)}
                    >
                      공유 링크 관리
                    </Button>
                  </div>
                )}
                {viewMode === 'board' ? (
                  <KanbanBoard
                    tasks={tasks || []}
                    onTaskClick={(task) => setSelectedTask(task)}
                    onTaskStatusChange={(taskId, newStatus) => {
                      updateTaskMutation.mutate({ taskId, data: { status: newStatus } });
                    }}
                    isDragDisabled={myRole === 'viewer'}
                  />
                ) : (
                  <TaskTableView
                    tasks={tasks || []}
                    onTaskClick={(task) => setSelectedTask(task)}
                  />
                )}
              </>
            )
          ) : isWeekLoading ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-muted-foreground font-medium">로딩 중...</p>
            </div>
          ) : (
            <>
              <h2 className="text-lg sm:text-xl font-black mb-4">내 주간 태스크</h2>
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
      {selectedProjectId && user && (
        <TaskModal
          mode="create"
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

      {selectedProjectId && user && myRole === 'owner' && (
        <ProjectMemberManager
          projectId={selectedProjectId}
          currentUserId={user.id}
          isOpen={isProjectMemberModalOpen}
          onClose={() => setProjectMemberModalOpen(false)}
        />
      )}

      {selectedProjectId && myRole === 'owner' && (
        <ShareLinkManager
          projectId={selectedProjectId}
          projectName={selectedProject?.name || ''}
          isOpen={isShareManagerOpen}
          onClose={() => setShareManagerOpen(false)}
        />
      )}

      <TaskModal
        mode="edit"
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
