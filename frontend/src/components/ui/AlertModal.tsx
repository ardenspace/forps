import { Button } from '@/components/ui/button';

interface AlertModalProps {
  isOpen: boolean;
  title: string;
  description?: string;
  confirmText?: string;
  onClose: () => void;
}

export function AlertModal({
  isOpen,
  title,
  description,
  confirmText = '확인',
  onClose,
}: AlertModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="w-full max-w-sm bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-black text-base mb-2">{title}</h3>
        {description && <p className="text-sm text-muted-foreground mb-4">{description}</p>}
        <div className="flex justify-end">
          <Button type="button" onClick={onClose}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
