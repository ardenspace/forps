import { useMemo } from 'react';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  useActivateShareLink,
  useCreateShareLink,
  useDeactivateShareLink,
  useDeleteShareLink,
  useShareLinks,
} from '@/hooks/useShareLinks';
import type { ShareLink } from '@/types';

interface ShareLinkManagerProps {
  projectId: string;
  projectName: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ShareLinkManager({ projectId, projectName, isOpen, onClose }: ShareLinkManagerProps) {
  const { data: links, isLoading } = useShareLinks(isOpen ? projectId : null);
  const createShareLink = useCreateShareLink(projectId);
  const deactivateShareLink = useDeactivateShareLink(projectId);
  const activateShareLink = useActivateShareLink(projectId);
  const deleteShareLink = useDeleteShareLink(projectId);

  const baseUrl = useMemo(() => {
    if (typeof window !== 'undefined') {
      return window.location.origin;
    }
    return '';
  }, []);

  const handleCreateLink = async () => {
    await createShareLink.mutateAsync({ scope: 'project_read' });
  };

  const handleDeactivate = async (linkId: string) => {
    await deactivateShareLink.mutateAsync(linkId);
  };

  const handleActivate = async (linkId: string) => {
    await activateShareLink.mutateAsync(linkId);
  };

  const handleDelete = async (linkId: string) => {
    await deleteShareLink.mutateAsync(linkId);
  };

  const copyLink = async (link: ShareLink) => {
    const url = `${baseUrl}/share/${link.token}`;
    await navigator.clipboard.writeText(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-3 sm:p-4">
      <div className="bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-4 sm:p-6 w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-black text-base sm:text-lg">공유 링크 관리</h2>
            <p className="text-xs sm:text-sm text-muted-foreground break-words">{projectName}</p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>닫기</Button>
        </div>

        <div className="mb-4">
          <Button
            type="button"
            onClick={handleCreateLink}
            disabled={createShareLink.isPending}
            className="border-2 border-black font-bold"
          >
            {createShareLink.isPending ? '생성 중...' : '새 공유 링크 생성'}
          </Button>
        </div>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">로딩 중...</p>
        ) : (
          <div className="space-y-3">
            {links?.map((link) => {
              const shareUrl = `${baseUrl}/share/${link.token}`;
              const isMutating =
                deactivateShareLink.isPending ||
                activateShareLink.isPending ||
                deleteShareLink.isPending;

              return (
                <div key={link.id} className="border-2 border-black p-3 bg-yellow-50">
                  <p className="text-xs text-muted-foreground mb-1">공유 URL</p>
                  <p className="text-sm font-mono break-all mb-2">{shareUrl}</p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                    <span>{link.is_active ? '활성' : '비활성'}</span>
                    <span>•</span>
                    <span>만료: {new Date(link.expires_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => copyLink(link)}
                        disabled={isMutating}
                      >
                        복사
                      </Button>
                      {link.is_active ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeactivate(link.id)}
                          disabled={isMutating}
                        >
                          철회
                        </Button>
                      ) : (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => handleActivate(link.id)}
                          disabled={isMutating}
                        >
                          재활성화
                        </Button>
                      )}
                    </div>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      onClick={() => handleDelete(link.id)}
                      disabled={isMutating}
                      className="h-9 w-9 border-0 bg-transparent p-0 text-red-600 hover:bg-transparent hover:text-red-600"
                      aria-label="공유 링크 삭제"
                    >
                      <Trash2 strokeWidth={2.8} />
                    </Button>
                  </div>
                </div>
              );
            })}
            {!links?.length && (
              <p className="text-sm text-muted-foreground text-center py-6">생성된 공유 링크가 없습니다.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
