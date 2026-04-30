import { useEffect, useState } from 'react';
import {
  useGitSettings,
  useRegisterWebhook,
  useUpdateGitSettings,
} from '@/hooks/useGithubSettings';

interface ProjectGitSettingsModalProps {
  projectId: string;
  open: boolean;
  onClose: () => void;
}

export function ProjectGitSettingsModal({
  projectId,
  open,
  onClose,
}: ProjectGitSettingsModalProps) {
  const { data: settings, isLoading } = useGitSettings(open ? projectId : null);
  const updateMutation = useUpdateGitSettings(projectId);
  const registerMutation = useRegisterWebhook(projectId);

  const [repoUrl, setRepoUrl] = useState('');
  const [planPath, setPlanPath] = useState('PLAN.md');
  const [handoffDir, setHandoffDir] = useState('handoffs/');
  const [pat, setPat] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (settings) {
      setRepoUrl(settings.git_repo_url ?? '');
      setPlanPath(settings.plan_path);
      setHandoffDir(settings.handoff_dir);
    }
  }, [settings]);

  if (!open) return null;

  const handleSave = async () => {
    setError(null);
    setFeedback(null);
    try {
      await updateMutation.mutateAsync({
        git_repo_url: repoUrl || null,
        plan_path: planPath,
        handoff_dir: handoffDir,
        ...(pat ? { github_pat: pat } : {}),
      });
      setPat('');
      setFeedback('저장됨');
    } catch (e) {
      setError(e instanceof Error ? e.message : '저장 실패');
    }
  };

  const handleRegisterWebhook = async () => {
    setError(null);
    setFeedback(null);
    try {
      const res = await registerMutation.mutateAsync();
      setFeedback(
        res.was_existing
          ? `기존 webhook 갱신 (secret rotated, hook_id=${res.webhook_id})`
          : `webhook 신규 등록 완료 (hook_id=${res.webhook_id})`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'webhook 등록 실패');
    }
  };

  const webhookDisabled = !settings?.git_repo_url || !settings?.has_github_pat;

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-3 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-4 sm:p-6 w-full max-w-md max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-black text-base sm:text-lg mb-4">Git 연동 설정</h2>

        {isLoading ? (
          <p className="text-sm text-muted-foreground py-4">불러오는 중...</p>
        ) : (
          <div className="space-y-4">
            {/* repo URL */}
            <div>
              <label className="font-bold text-sm block mb-1">저장소 URL</label>
              <input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>

            {/* PLAN.md 경로 */}
            <div>
              <label className="font-bold text-sm block mb-1">PLAN.md 경로</label>
              <input
                value={planPath}
                onChange={(e) => setPlanPath(e.target.value)}
                placeholder="PLAN.md"
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>

            {/* handoff 디렉토리 */}
            <div>
              <label className="font-bold text-sm block mb-1">Handoff 디렉토리</label>
              <input
                value={handoffDir}
                onChange={(e) => setHandoffDir(e.target.value)}
                placeholder="handoffs/"
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
            </div>

            {/* GitHub PAT */}
            <div>
              <label className="font-bold text-sm block mb-1">GitHub PAT</label>
              <input
                type="password"
                value={pat}
                onChange={(e) => setPat(e.target.value)}
                placeholder={settings?.has_github_pat ? '변경 시에만 입력' : 'ghp_...'}
                className="border-2 border-black rounded-none w-full px-3 py-2 text-sm focus:outline-none focus:shadow-[2px_2px_0px_0px_rgba(244,0,4,1)]"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                <code className="bg-gray-100 px-1">admin:repo_hook</code> 스코프 필요 —{' '}
                <a
                  href="https://github.com/settings/tokens/new?scopes=admin:repo_hook"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-black"
                >
                  토큰 발급
                </a>
              </p>
            </div>

            {/* 구분선 */}
            <hr className="border-black border-t-2" />

            {/* Webhook 섹션 */}
            <div>
              <p className="font-bold text-sm mb-2">Webhook 상태</p>
              <p className="text-xs text-muted-foreground mb-1">
                {settings?.has_webhook_secret ? '✓ 등록됨' : '미등록'}
              </p>
              {settings?.public_webhook_url && (
                <p className="text-[11px] font-mono bg-gray-100 border border-gray-300 px-2 py-1 break-all mb-2">
                  {settings.public_webhook_url}
                </p>
              )}
              <button
                type="button"
                disabled={webhookDisabled || registerMutation.isPending}
                onClick={handleRegisterWebhook}
                className="border-2 border-black font-bold px-3 py-1.5 text-xs hover:bg-yellow-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {registerMutation.isPending
                  ? '등록 중...'
                  : settings?.has_webhook_secret
                    ? '재등록 (secret rotate)'
                    : '등록'}
              </button>
              {webhookDisabled && (
                <p className="text-[11px] text-muted-foreground mt-1">
                  저장소 URL과 PAT 를 먼저 저장해야 합니다.
                </p>
              )}
            </div>

            {/* 피드백 메시지 */}
            {error && (
              <p className="text-xs text-red-600 font-medium">{error}</p>
            )}
            {feedback && (
              <p className="text-xs text-green-600 font-medium">{feedback}</p>
            )}
          </div>
        )}

        {/* 푸터 버튼 */}
        <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="border-2 border-black font-bold px-4 py-2 text-xs sm:text-sm hover:bg-yellow-100 transition-colors w-full sm:w-auto"
          >
            닫기
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={updateMutation.isPending || isLoading}
            className="bg-black text-white border-2 border-black font-bold px-4 py-2 text-xs sm:text-sm hover:bg-yellow-400 hover:text-black transition-colors shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] disabled:opacity-50 w-full sm:w-auto"
          >
            {updateMutation.isPending ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>
    </div>
  );
}
