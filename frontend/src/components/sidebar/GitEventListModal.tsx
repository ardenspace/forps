import { useFailedGitEvents, useReprocessEvent } from '@/hooks/useGithubSettings';
import type { GitEventSummary } from '@/types/git';

interface GitEventListModalProps {
  projectId: string;
  open: boolean;
  onClose: () => void;
}

export function GitEventListModal({ projectId, open, onClose }: GitEventListModalProps) {
  const { data: events, isLoading } = useFailedGitEvents(open ? projectId : null);
  const reprocess = useReprocessEvent(projectId);

  if (!open) return null;

  const handleReprocess = async (eventId: string) => {
    try {
      await reprocess.mutateAsync(eventId);
      // onSuccess invalidate 가 자동 refetch — 토스트 자리는 후속 (현재 없음)
    } catch (err: unknown) {
      // 토스트 system 미도입 — alert 로 대체 (Phase 5b 패턴)
      const error = err as { response?: { status?: number; data?: { detail?: string } }; message?: string };
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      if (status === 409) {
        alert('처리 중입니다 — 잠시 후 다시 시도해 주세요');
      } else if (status === 400) {
        alert('이미 성공적으로 처리되었습니다');
      } else {
        alert(detail || error.message || '재처리 실패');
      }
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-3 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-4 sm:p-6 w-full max-w-2xl max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-black text-base sm:text-lg mb-4">⚠️ Sync 실패 이벤트</h2>

        {isLoading ? (
          <p className="text-sm text-muted-foreground py-4">불러오는 중...</p>
        ) : !events || events.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            실패한 sync 이벤트가 없습니다.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs sm:text-sm">
              <thead className="border-b-2 border-black">
                <tr className="font-bold">
                  <th className="text-left py-2 pr-2">시각</th>
                  <th className="text-left py-2 pr-2">브랜치</th>
                  <th className="text-left py-2 pr-2">commit</th>
                  <th className="text-left py-2 pr-2">error</th>
                  <th className="text-left py-2">동작</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <EventRow
                    key={e.id}
                    event={e}
                    onReprocess={handleReprocess}
                    isPending={reprocess.isPending && reprocess.variables === e.id}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex justify-end mt-4">
          <button
            type="button"
            className="px-3 py-1.5 text-xs font-medium border-2 border-black hover:bg-yellow-50 transition-colors"
            onClick={onClose}
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

interface EventRowProps {
  event: GitEventSummary;
  onReprocess: (eventId: string) => void;
  isPending: boolean;
}

function EventRow({ event, onReprocess, isPending }: EventRowProps) {
  const date = new Date(event.received_at);
  const timeStr = `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  const errorOneLine = (event.error || '').split('\n')[0].slice(0, 50);
  return (
    <tr className="border-b border-gray-200">
      <td className="py-2 pr-2 whitespace-nowrap">{timeStr}</td>
      <td className="py-2 pr-2 break-all">{event.branch}</td>
      <td className="py-2 pr-2 font-mono">{event.head_commit_sha.slice(0, 7)}</td>
      <td className="py-2 pr-2 text-red-700" title={event.error || ''}>{errorOneLine}</td>
      <td className="py-2">
        <button
          type="button"
          disabled={isPending}
          onClick={() => onReprocess(event.id)}
          className="px-2 py-1 text-[11px] font-medium border-2 border-black bg-white hover:bg-yellow-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isPending ? '처리 중...' : '재처리'}
        </button>
      </td>
    </tr>
  );
}
