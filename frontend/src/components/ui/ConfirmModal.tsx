import { Button } from '@/components/ui/button';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  confirmVariant?: 'default' | 'destructive';
  isConfirming?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmModal({
  isOpen,
  title,
  description,
  confirmText = '확인',
  cancelText = '취소',
  confirmVariant = 'destructive',
  isConfirming = false,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] bg-black/60 flex items-center justify-center p-4" onClick={onCancel}>
      <div
        className="w-full max-w-sm bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-black text-base mb-2">{title}</h3>
        {description && <p className="text-sm text-muted-foreground mb-4">{description}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isConfirming}>
            {cancelText}
          </Button>
          <Button type="button" variant={confirmVariant} onClick={onConfirm} disabled={isConfirming}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
