import { useErrorGroupDetail, useTransitionErrorStatus } from '@/hooks/useErrorGroups';
import type { ErrorGroupAction, ErrorGroupStatus } from '@/types/error';
import { Button } from '@/components/ui/button';
import { GitContextPanel } from './GitContextPanel';
import { LogLevelBadge } from './LogLevelBadge';

interface ErrorDetailProps {
  projectId: string;
  groupId: string;
  isOwner: boolean;
  defaultResolveSha: string | null;  // 프로젝트의 last_synced_commit_sha
  onBack: () => void;
}

const STATUS_STYLES: Record<ErrorGroupStatus, string> = {
  open: 'bg-red-100 text-red-800 border-red-500',
  resolved: 'bg-green-100 text-green-800 border-green-500',
  ignored: 'bg-gray-100 text-gray-700 border-gray-500',
  regressed: 'bg-orange-100 text-orange-800 border-orange-500',
};

const ACTIONS_BY_STATUS: Record<ErrorGroupStatus, ErrorGroupAction[]> = {
  open: ['resolve', 'ignore'],
  resolved: ['reopen'],
  ignored: ['unmute'],
  regressed: ['resolve', 'reopen'],
};

const ACTION_LABEL: Record<ErrorGroupAction, string> = {
  resolve: '해결됨으로 표시',
  ignore: '무시',
  reopen: '다시 열기',
  unmute: '무시 해제',
};

export function ErrorDetail({
  projectId,
  groupId,
  isOwner,
  defaultResolveSha,
  onBack,
}: ErrorDetailProps) {
  const { data, isLoading, error } = useErrorGroupDetail(projectId, groupId);
  const transitionMutation = useTransitionErrorStatus(projectId);

  if (isLoading) {
    return <p className="text-muted-foreground font-medium">로딩 중...</p>;
  }
  if (error || !data) {
    return (
      <div className="border-2 border-black bg-white p-4 rounded">
        <p className="text-sm text-red-700 font-bold">에러 그룹을 불러올 수 없습니다.</p>
        <Button onClick={onBack} className="mt-2 border-2 border-black font-bold">
          ← 목록으로
        </Button>
      </div>
    );
  }

  const { group, recent_events, git_context } = data;
  const actions = ACTIONS_BY_STATUS[group.status];

  const handleAction = (action: ErrorGroupAction) => {
    transitionMutation.mutate({
      groupId: group.id,
      action,
      // resolve 일 때만 sha 채움. user 가 명시 입력 UI 는 v2.
      resolved_in_version_sha: action === 'resolve' ? defaultResolveSha ?? null : null,
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button onClick={onBack} className="border-2 border-black font-bold text-xs">
          ← 목록
        </Button>
        <span
          className={`px-2 py-0.5 text-[10px] font-bold uppercase border-2 rounded ${
            STATUS_STYLES[group.status]
          }`}
        >
          {group.status}
        </span>
        <span className="text-xs text-muted-foreground">
          누적 {group.event_count.toLocaleString()} 회
        </span>
      </div>

      <header className="border-2 border-black bg-white p-3 sm:p-4 shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] rounded">
        <h2 className="text-base sm:text-lg font-black break-words">
          {group.exception_class}
        </h2>
        {group.exception_message_sample && (
          <p className="mt-1 text-sm break-words text-muted-foreground">
            {group.exception_message_sample}
          </p>
        )}
        <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px] text-muted-foreground">
          <p>
            <span className="font-bold">최초:</span>{' '}
            {new Date(group.first_seen_at).toLocaleString()}
          </p>
          <p>
            <span className="font-bold">최근:</span>{' '}
            {new Date(group.last_seen_at).toLocaleString()}
          </p>
          {group.resolved_at && (
            <p>
              <span className="font-bold">해결됨:</span>{' '}
              {new Date(group.resolved_at).toLocaleString()}
              {group.resolved_in_version_sha && ` @ ${group.resolved_in_version_sha.slice(0, 8)}`}
            </p>
          )}
        </div>
      </header>

      {isOwner && actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <Button
              key={action}
              onClick={() => handleAction(action)}
              disabled={transitionMutation.isPending}
              className="border-2 border-black font-bold text-xs sm:text-sm"
            >
              {transitionMutation.isPending ? '처리 중...' : ACTION_LABEL[action]}
            </Button>
          ))}
        </div>
      )}

      <GitContextPanel context={git_context} firstSeenSha={group.first_seen_version_sha} />

      <section className="border-2 border-black bg-white p-3 sm:p-4 shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] rounded">
        <h3 className="text-sm sm:text-base font-black mb-2">
          최근 이벤트 ({recent_events.length})
        </h3>
        {recent_events.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">이벤트 없음</p>
        ) : (
          <ul className="space-y-2">
            {recent_events.map((evt) => (
              <li
                key={evt.id}
                className="border border-black/20 rounded p-2 bg-gray-50 text-xs space-y-1"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <LogLevelBadge level={evt.level} />
                  <code className="text-[10px] font-mono">{evt.logger_name}</code>
                  <span className="text-muted-foreground">·</span>
                  <code
                    className="text-[10px] font-mono"
                    title={evt.version_sha}
                  >
                    {evt.version_sha === 'unknown' ? 'unknown' : evt.version_sha.slice(0, 8)}
                  </code>
                  <span className="text-muted-foreground ml-auto">
                    {new Date(evt.received_at).toLocaleString()}
                  </span>
                </div>
                <p className="break-words">{evt.message}</p>
                {evt.exception_message && evt.exception_message !== evt.message && (
                  <p className="text-muted-foreground italic break-words">
                    {evt.exception_message}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
