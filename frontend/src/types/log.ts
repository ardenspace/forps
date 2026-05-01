// Backend LogLevel enum wire value
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export interface LogEventSummary {
  id: string;
  level: LogLevel;
  message: string;
  logger_name: string;
  version_sha: string;
  environment: string;
  hostname: string;
  emitted_at: string;
  received_at: string;
  fingerprint: string | null;
  exception_class: string | null;
  exception_message: string | null;
}

export interface LogEventListResponse {
  items: LogEventSummary[];
  total: number;
}
