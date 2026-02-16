import { useState, useEffect, useRef } from 'react';
import { useCreateTask, useUpdateTask } from '@/hooks/useTasks';
import type { Task, TaskStatus } from '@/types/task';
import type { WorkspaceRole } from '@/types/workspace';
import type { ProjectMember } from '@/types/project';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { DatePicker } from '@/components/ui/DatePicker';

interface TaskModalBaseProps {
  members: ProjectMember[];
  isOpen: boolean;
  onClose: () => void;
}

interface CreateModeProps extends TaskModalBaseProps {
  mode: 'create';
  projectId: string;
  currentUserId: string;
  task?: never;
  myRole?: never;
  onDelete?: never;
}

interface EditModeProps extends TaskModalBaseProps {
  mode: 'edit';
  task: Task | null;
  myRole: WorkspaceRole;
  onDelete?: (taskId: string) => void;
  projectId?: never;
  currentUserId?: never;
}

type TaskModalProps = CreateModeProps | EditModeProps;

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'todo', label: 'To Do' },
  { value: 'doing', label: 'Doing' },
  { value: 'done', label: 'Done' },
  { value: 'blocked', label: 'Blocked' },
];

const metaLabelClass = 'text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1 block';
const metaInputClass =
  'border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:bg-gray-100 disabled:cursor-not-allowed';

export function TaskModal(props: TaskModalProps) {
  const { members, isOpen, onClose } = props;
  const isCreateMode = props.mode === 'create';

  const createTask = useCreateTask(isCreateMode ? props.projectId : '');
  const updateTask = useUpdateTask();

  const modalRef = useRef<HTMLDivElement>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<TaskStatus>('todo');
  const [dueDate, setDueDate] = useState('');
  const [assigneeId, setAssigneeId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [showSaved, setShowSaved] = useState(false);

  const [original, setOriginal] = useState({
    title: '',
    description: '',
    status: 'todo' as TaskStatus,
    dueDate: '',
    assigneeId: null as string | null,
  });

  // Initialize form state
  useEffect(() => {
    if (!isOpen) return;

    if (isCreateMode) {
      // Create mode: reset to defaults
      setTitle('');
      setDescription('');
      setStatus('todo');
      setDueDate('');
      setAssigneeId(props.currentUserId);
      setIsSaving(false);
      setShowSaved(false);
    } else if (props.task) {
      // Edit mode: load task data
      const taskDueDate = props.task.due_date ? props.task.due_date.split('T')[0] : '';
      setTitle(props.task.title);
      setDescription(props.task.description || '');
      setStatus(props.task.status);
      setDueDate(taskDueDate);
      setAssigneeId(props.task.assignee_id);
      setOriginal({
        title: props.task.title,
        description: props.task.description || '',
        status: props.task.status,
        dueDate: taskDueDate,
        assigneeId: props.task.assignee_id,
      });
      setIsSaving(false);
      setShowSaved(false);
    }
  }, [isOpen, isCreateMode, isCreateMode ? props.currentUserId : props.task]);

  const canEdit = isCreateMode || props.myRole === 'owner' || props.myRole === 'editor';
  const canDelete = !isCreateMode && props.myRole === 'owner';
  const task = isCreateMode ? null : props.task;

  if (!isOpen) return null;
  if (!isCreateMode && !task) return null;

  const hasChanges =
    title !== original.title ||
    description !== original.description ||
    status !== original.status ||
    dueDate !== original.dueDate ||
    assigneeId !== original.assigneeId;

  const handleCreate = async () => {
    if (!title.trim()) return;
    setIsSaving(true);
    try {
      await createTask.mutateAsync({
        title,
        description: description || undefined,
        status,
        due_date: dueDate || undefined,
        assignee_id: assigneeId || undefined,
      });
      onClose();
    } catch {
      // keep modal open on error
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = async () => {
    if (isSaving) return;

    if (isCreateMode) {
      onClose();
      return;
    }

    // Edit mode: auto-save on close if changed
    if (hasChanges && canEdit && task) {
      setIsSaving(true);
      try {
        await updateTask.mutateAsync({
          taskId: task.id,
          data: {
            title,
            description: description || null,
            status,
            due_date: dueDate || null,
            assignee_id: assigneeId,
          },
        });
        setShowSaved(true);
        setTimeout(() => {
          setIsSaving(false);
          onClose();
        }, 400);
      } catch {
        setIsSaving(false);
        onClose();
      }
    } else {
      onClose();
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
      handleClose();
    }
  };

  const memberOptions = [
    { value: '', label: '담당자 없음' },
    ...members.map((m) => {
      const isSelf = isCreateMode && m.user_id === props.currentUserId;
      return {
        value: m.user_id,
        label: isSelf ? `${m.user.name} (나)` : m.user.name,
      };
    }),
  ];

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div
        ref={modalRef}
        className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] w-full max-w-3xl"
      >
        <div className="p-6 pt-6">
          {/* 2-column body */}
          <div className="flex gap-6">
            {/* Left: title + description */}
            <div className="flex-1 flex flex-col gap-4 min-w-0">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={!canEdit || isSaving}
                placeholder="태스크 제목"
                className="border-0 border-b-2 border-black rounded-none w-full px-0 py-2 font-black text-xl focus:outline-none bg-transparent disabled:bg-transparent placeholder:text-gray-400"
                autoFocus={isCreateMode}
              />

              <div>
                <label className={metaLabelClass}>설명</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={!canEdit || isSaving}
                  placeholder="설명 (선택)"
                  className={`${metaInputClass} min-h-[280px] resize-none`}
                />
              </div>
            </div>

            {/* Right: metadata */}
            <div className="w-56 flex-shrink-0 flex flex-col gap-4 border-l-2 border-black pl-6">
              <div>
                <label className={metaLabelClass}>상태</label>
                <CustomSelect
                  value={status}
                  onChange={(v) => setStatus(v as TaskStatus)}
                  options={statusOptions}
                  disabled={!canEdit || isSaving}
                />
              </div>

              <div>
                <label className={metaLabelClass}>담당자</label>
                <CustomSelect
                  value={assigneeId || ''}
                  onChange={(v) => setAssigneeId(v || null)}
                  options={memberOptions}
                  disabled={!canEdit || isSaving}
                />
              </div>

              <div>
                <label className={metaLabelClass}>마감일</label>
                <DatePicker
                  value={dueDate}
                  onChange={setDueDate}
                  disabled={!canEdit || isSaving}
                  placeholder="날짜 선택"
                />
              </div>

              {!canEdit && (
                <div className="mt-auto">
                  <span className="text-xs bg-yellow-200 text-black border-2 border-black font-bold px-2 py-1 inline-block">
                    읽기 전용
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t-2 border-black">
            <div>
              {canDelete && !isCreateMode && props.onDelete && task && (
                <button
                  type="button"
                  disabled={isSaving}
                  onClick={() => {
                    if (confirm('정말 삭제하시겠습니까?')) {
                      props.onDelete!(task.id);
                      onClose();
                    }
                  }}
                  className="bg-red-500 text-white border-2 border-black font-bold px-4 py-2 text-sm hover:bg-red-600 transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50"
                >
                  삭제
                </button>
              )}
            </div>

            <div className="flex-1 flex justify-center">
              {isSaving && !showSaved && (
                <span className="text-xs font-bold text-muted-foreground">
                  {isCreateMode ? '생성 중...' : '저장 중...'}
                </span>
              )}
              {showSaved && (
                <span className="text-xs font-bold text-green-700">저장됨 ✓</span>
              )}
            </div>

            <div className="flex gap-2">
              {isCreateMode ? (
                <>
                  <button
                    type="button"
                    onClick={handleClose}
                    disabled={isSaving}
                    className="border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-100 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    type="button"
                    onClick={handleCreate}
                    disabled={isSaving || !title.trim()}
                    className="bg-black text-white border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50"
                  >
                    생성
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSaving}
                  className="border-2 border-black font-bold px-4 py-2 text-sm hover:bg-yellow-100 transition-colors"
                >
                  닫기
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
