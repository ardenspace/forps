export interface User {
  id: string;
  email: string;
  username: string | null;
  name: string;
  created_at: string;
}

export interface UserBrief {
  id: string;
  name: string;
  email: string;
}

export interface UserUpdateRequest {
  username?: string | null;
}

// PLAN.md `@username` 멘션 매핑 — backend USERNAME_PATTERN 와 동일
export const USERNAME_PATTERN = /^[a-z0-9_-]{2,32}$/;
