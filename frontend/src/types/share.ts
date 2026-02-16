export interface SharedTask {
  id: string;
  title: string;
  status: string;
  due_date: string | null;
  assignee_name: string | null;
}

export interface SharedProjectData {
  project_name: string;
  tasks: SharedTask[];
}

export interface ShareLink {
  id: string;
  project_id: string;
  created_by: string;
  token: string;
  scope: 'project_read' | 'task_read';
  is_active: boolean;
  expires_at: string;
  created_at: string;
}

export interface ShareLinkCreateRequest {
  scope?: 'project_read' | 'task_read';
}
