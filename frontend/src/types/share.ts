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
