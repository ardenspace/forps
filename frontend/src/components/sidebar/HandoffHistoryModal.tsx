import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useHandoffs } from '@/hooks/useGithubSettings';

interface HandoffHistoryModalProps {
  projectId: string;
  open: boolean;
  onClose: () => void;
}

export function HandoffHistoryModal({
  projectId,
  open,
  onClose,
}: HandoffHistoryModalProps) {
  const [branchFilter, setBranchFilter] = useState('');
  const params = branchFilter ? { branch: branchFilter, limit: 100 } : { limit: 100 };
  const { data: handoffs, isLoading } = useHandoffs(open ? projectId : null, params);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 bg-brand-coffee/20 backdrop-blur-sm flex items-center justify-center z-50 p-3 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-brand-cream rounded-3xl shadow-xl border border-brand-blue/10 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col p-4 sm:p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-bold text-base text-brand-blue sm:text-lg mb-4 shrink-0">Handoff 이력</h2>

        <div className="overflow-y-auto w-full flex-1 min-h-0 pr-2 -mr-2">
          {/* 브랜치 필터 */}
          <div className="mb-4">
            <label className="font-bold text-sm block mb-1">브랜치 필터</label>
            <input
              value={branchFilter}
              onChange={(e) => setBranchFilter(e.target.value)}
              placeholder="main, feature/xxx ..."
              className="border border-brand-blue/20 rounded-xl w-full px-3 py-2 text-sm focus:outline-none focus:shadow-sm"
            />
          </div>

          {isLoading ? (
            <p className="text-sm text-muted-foreground py-4">불러오는 중...</p>
          ) : !handoffs || handoffs.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4">
              handoff 이력 없음 — webhook 설정 후 첫 push 가 들어오면 여기 표시됩니다.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-brand-blue/20">
                    <th className="text-left font-bold px-2 py-1.5">날짜</th>
                    <th className="text-left font-bold px-2 py-1.5">브랜치</th>
                    <th className="text-left font-bold px-2 py-1.5">작성자</th>
                    <th className="text-left font-bold px-2 py-1.5">commit</th>
                    <th className="text-right font-bold px-2 py-1.5">tasks</th>
                  </tr>
                </thead>
                <tbody>
                  {handoffs.map((h) => (
                    <tr
                      key={h.id}
                      className="border-b border-gray-200 hover:bg-white/50 transition-colors"
                    >
                      <td className="px-2 py-1.5 whitespace-nowrap">
                        {new Date(h.pushed_at).toLocaleString('ko-KR', {
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td className="px-2 py-1.5 font-mono">{h.branch}</td>
                      <td className="px-2 py-1.5">@{h.author_git_login}</td>
                      <td className="px-2 py-1.5 font-mono">{h.commit_sha.slice(0, 7)}</td>
                      <td className="px-2 py-1.5 text-right">{h.parsed_tasks_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 푸터 */}
          <div className="flex justify-end mt-6">
            <button
              type="button"
              onClick={onClose}
              className="border border-brand-blue/20 font-bold px-4 py-2 text-xs sm:text-sm hover:bg-white/60 transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
