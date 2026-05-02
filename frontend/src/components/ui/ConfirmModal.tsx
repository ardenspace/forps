import { createPortal } from 'react-dom';
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

  return createPortal(
    <div className="fixed inset-0 z-[70] bg-brand-coffee/20 backdrop-blur-sm flex items-center justify-center p-4" onClick={onCancel}>
      <div
        className="w-full max-w-sm bg-brand-cream rounded-3xl shadow-xl border border-brand-blue/10 p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-bold text-base text-brand-blue mb-2">{title}</h3>
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
    </div>,
    document.body
  );
}
