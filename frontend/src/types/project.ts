import type { WorkspaceRole } from './workspace';
import type { UserBrief } from './user';

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

export interface ProjectMember {
  id: string;
  user_id: string;
  role: WorkspaceRole;
  created_at: string;
  user: UserBrief;
}

export interface AddProjectMemberRequest {
  email: string;
  role: WorkspaceRole;
}

export interface UpdateProjectMemberRequest {
  role: WorkspaceRole;
}
