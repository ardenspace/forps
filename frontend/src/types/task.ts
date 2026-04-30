import type { UserBrief } from './user';

export const TASK_STATUS = {
  TODO: 'todo',
  DOING: 'doing',
  DONE: 'done',
  BLOCKED: 'blocked',
} as const;

export type TaskStatus = (typeof TASK_STATUS)[keyof typeof TASK_STATUS];

export const TASK_SOURCE = {
  MANUAL: 'manual',
  SYNCED_FROM_PLAN: 'synced_from_plan',
} as const;

export type TaskSource = (typeof TASK_SOURCE)[keyof typeof TASK_SOURCE];

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  due_date: string | null;
  assignee_id: string | null;
  reporter_id: string | null;
  created_at: string;
  updated_at: string;
  assignee: UserBrief | null;
  reporter: UserBrief | null;
  // Phase 5b — backend Phase 1 모델 필드 노출
  source: TaskSource;
  external_id: string | null;
  last_commit_sha: string | null;
  archived_at: string | null;
}

export interface TaskCreate {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  due_date?: string | null;
  assignee_id?: string | null;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  due_date?: string | null;
  assignee_id?: string | null;
}
