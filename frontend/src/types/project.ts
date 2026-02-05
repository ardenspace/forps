import type { WorkspaceRole } from './workspace';

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  my_role: WorkspaceRole;
  task_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}
