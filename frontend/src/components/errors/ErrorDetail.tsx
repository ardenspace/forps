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
  open: 'bg-brand-orange/20 text-brand-coffee border-brand-orange/50',
  resolved: 'bg-brand-neon/20 text-brand-coffee border-brand-neon/50',
  ignored: 'bg-black/5 text-brand-blue border-brand-blue/20',
  regressed: 'bg-brand-orange/40 text-brand-coffee border-brand-orange',
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
      <div className="glass-panel p-6 rounded-2xl text-center">
        <p className="text-sm text-brand-orange font-bold">에러 그룹을 불러올 수 없습니다.</p>
        <Button onClick={onBack} variant="outline" className="mt-4 rounded-full border-brand-blue/30 text-brand-blue hover:bg-brand-sky/20 font-bold">
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
      <div className="flex items-center gap-3">
        <Button onClick={onBack} variant="outline" size="sm" className="rounded-full bg-white/50 border-white/60 text-brand-blue hover:bg-white/80 font-bold text-xs shadow-sm">
          ← 목록
        </Button>
        <span
          className={`px-2 py-0.5 text-[10px] font-bold uppercase border rounded-md ${
            STATUS_STYLES[group.status]
          }`}
        >
          {group.status}
        </span>
        <span className="text-xs text-brand-blue/70">
          누적 {group.event_count.toLocaleString()} 회
        </span>
      </div>

      <header className="glass-panel p-5 sm:p-6 shadow-sm rounded-2xl">
        <h2 className="text-base sm:text-lg font-bold break-words text-brand-blue">
          {group.exception_class}
        </h2>
        {group.exception_message_sample && (
          <p className="mt-2 text-sm break-words text-brand-blue/80">
            {group.exception_message_sample}
          </p>
        )}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-brand-blue/60">
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
              className="rounded-full bg-brand-neon text-brand-coffee border border-brand-neon/50 hover:brightness-110 font-bold text-xs sm:text-sm shadow-sm px-5"
            >
              {transitionMutation.isPending ? '처리 중...' : ACTION_LABEL[action]}
            </Button>
          ))}
        </div>
      )}

      <GitContextPanel context={git_context} firstSeenSha={group.first_seen_version_sha} />

      <section className="glass-panel p-5 sm:p-6 shadow-sm rounded-2xl">
        <h3 className="text-sm sm:text-base font-bold mb-4 text-brand-blue">
          최근 이벤트 ({recent_events.length})
        </h3>
        {recent_events.length === 0 ? (
          <p className="text-xs text-brand-blue/60 italic">이벤트 없음</p>
        ) : (
          <ul className="space-y-3">
            {recent_events.map((evt) => (
              <li
                key={evt.id}
                className="border border-white/60 rounded-xl p-4 glass shadow-sm text-xs space-y-2 text-brand-blue"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <LogLevelBadge level={evt.level} />
                  <code className="text-[10px] font-mono">{evt.logger_name}</code>
                  <span className="text-brand-blue/40">·</span>
                  <code
                    className="text-[10px] font-mono bg-white/50 px-1 rounded"
                    title={evt.version_sha}
                  >
                    {evt.version_sha === 'unknown' ? 'unknown' : evt.version_sha.slice(0, 8)}
                  </code>
                  <span className="text-brand-blue/60 ml-auto">
                    {new Date(evt.received_at).toLocaleString()}
                  </span>
                </div>
                <p className="break-words text-brand-coffee">{evt.message}</p>
                {evt.exception_message && evt.exception_message !== evt.message && (
                  <p className="text-brand-orange/80 italic break-words">
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
