import type { GitContextWrapper } from '@/types/error';

interface GitContextPanelProps {
  context: GitContextWrapper;
  firstSeenSha: string;
}

const SHORT_SHA = (sha: string) => sha.slice(0, 8);

function ShaBadge({ sha, label }: { sha: string; label?: string }) {
  if (sha === 'unknown') {
    return (
      <span className="inline-block px-1.5 py-0.5 text-[10px] font-mono border-2 border-yellow-500 bg-white/60 text-yellow-800 rounded">
        unknown {label ? `(${label})` : ''}
      </span>
    );
  }
  return (
    <code
      className="inline-block px-1.5 py-0.5 text-[10px] font-mono border border-brand-blue/20/20 bg-white rounded"
      title={sha}
    >
      {SHORT_SHA(sha)}
    </code>
  );
}

export function GitContextPanel({ context, firstSeenSha }: GitContextPanelProps) {
  const { first_seen, previous_good_sha } = context;
  const hasAny =
    first_seen.handoffs.length > 0 ||
    first_seen.tasks.length > 0 ||
    first_seen.git_push_event !== null;

  return (
    <section className="border border-brand-blue/20 bg-white p-3 sm:p-4 shadow-sm rounded">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm sm:text-base font-black">Git 컨텍스트</h3>
        <ShaBadge sha={firstSeenSha} label="first seen" />
      </div>

      {!hasAny && (
        <p className="text-xs text-muted-foreground italic mb-3">
          이 SHA 에 대응되는 git 동기화 데이터가 없습니다.
        </p>
      )}

      {first_seen.git_push_event && (
        <div className="mb-3">
          <p className="text-[10px] text-muted-foreground font-bold mb-1">PUSH 이벤트</p>
          <div className="border border-brand-blue/20/20 rounded p-2 bg-gray-50 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <ShaBadge sha={first_seen.git_push_event.head_commit_sha} />
              <span className="text-muted-foreground">on</span>
              <code className="text-[11px] font-mono">{first_seen.git_push_event.branch}</code>
              <span className="text-muted-foreground">by</span>
              <span className="font-medium">{first_seen.git_push_event.pusher}</span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1">
              {new Date(first_seen.git_push_event.received_at).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {first_seen.handoffs.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] text-muted-foreground font-bold mb-1">
            HANDOFF ({first_seen.handoffs.length})
          </p>
          <ul className="space-y-1">
            {first_seen.handoffs.map((h) => (
              <li key={h.id} className="border border-brand-blue/20/20 rounded p-2 bg-gray-50 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <ShaBadge sha={h.commit_sha} />
                  <code className="text-[11px] font-mono">{h.branch}</code>
                  <span className="font-medium">{h.author_git_login}</span>
                </div>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {new Date(h.pushed_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {first_seen.tasks.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] text-muted-foreground font-bold mb-1">
            TASK ({first_seen.tasks.length})
          </p>
          <ul className="space-y-1">
            {first_seen.tasks.map((t) => (
              <li key={t.id} className="border border-brand-blue/20/20 rounded p-2 bg-gray-50 text-xs">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold">{t.title}</span>
                  {t.archived_at && (
                    <span className="text-[10px] px-1 py-0.5 rounded bg-gray-200 text-gray-700 border border-gray-400">
                      archived
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {t.external_id ? `${t.external_id} · ` : ''}status: {t.status}
                  {t.last_commit_sha ? ` · ` : ''}
                  {t.last_commit_sha && <ShaBadge sha={t.last_commit_sha} />}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 pt-2 border-t border-brand-blue/20/10">
        <p className="text-[10px] text-muted-foreground font-bold mb-1">직전 정상 SHA</p>
        {previous_good_sha ? (
          <ShaBadge sha={previous_good_sha} label="last clean" />
        ) : (
          <span className="text-xs text-muted-foreground italic">
            없음 (이 fingerprint 의 첫 발생 이전 정상 이벤트 미존재)
          </span>
        )}
      </div>
    </section>
  );
}
