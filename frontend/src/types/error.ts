// ErrorGroup status transition action (PATCH request body)
export type ErrorGroupAction = 'resolve' | 'ignore' | 'reopen' | 'unmute';

// Backend ErrorGroupStatus enum wire value
export type ErrorGroupStatus = 'open' | 'resolved' | 'ignored' | 'regressed';

export interface ErrorGroupSummary {
  id: string;
  fingerprint: string;
  exception_class: string;
  exception_message_sample: string | null;
  event_count: number;
  status: ErrorGroupStatus;
  first_seen_at: string;          // ISO datetime
  first_seen_version_sha: string;
  last_seen_at: string;
  last_seen_version_sha: string;
  // Phase 5 Backend Task 3 fix #7 — audit fields
  resolved_at: string | null;
  resolved_by_user_id: string | null;
  resolved_in_version_sha: string | null;
}

export interface ErrorGroupListResponse {
  items: ErrorGroupSummary[];
  total: number;
}

// GET /errors/{id} response — git context nested
export interface HandoffRef {
  id: string;
  commit_sha: string;
  branch: string;
  author_git_login: string;
  pushed_at: string;
}

export interface TaskRef {
  id: string;
  external_id: string | null;
  title: string;
  status: string;
  last_commit_sha: string | null;
  archived_at: string | null;     // if not null, render archived badge
}

export interface GitPushEventRef {
  id: string;
  head_commit_sha: string;
  branch: string;
  pusher: string;
  received_at: string;
}

export interface GitContextBundle {
  handoffs: HandoffRef[];
  tasks: TaskRef[];
  git_push_event: GitPushEventRef | null;
}

export interface GitContextWrapper {
  first_seen: GitContextBundle;
  previous_good_sha: string | null;
}

export interface ErrorGroupDetail {
  group: ErrorGroupSummary;
  recent_events: import('./log').LogEventSummary[];
  git_context: GitContextWrapper;
}

// PATCH /errors/{id} request body
export interface ErrorGroupStatusUpdateRequest {
  action: ErrorGroupAction;
  resolved_in_version_sha?: string | null;
}
