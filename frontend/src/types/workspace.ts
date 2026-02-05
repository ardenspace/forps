export type WorkspaceRole = 'owner' | 'editor' | 'viewer';

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  my_role: WorkspaceRole;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreate {
  name: string;
  slug: string;
  description?: string;
}

export interface WorkspaceMember {
  id: string;
  user_id: string;
  role: WorkspaceRole;
  created_at: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export interface AddMemberRequest {
  email: string;
  role: WorkspaceRole;
}
