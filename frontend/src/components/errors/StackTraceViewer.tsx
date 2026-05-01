interface StackTraceViewerProps {
  trace: string | null;
  defaultOpen?: boolean;
}

export function StackTraceViewer({ trace, defaultOpen = false }: StackTraceViewerProps) {
  if (!trace) {
    return <p className="text-xs text-muted-foreground italic">스택 trace 없음</p>;
  }
  return (
    <details
      className="border-2 border-black/20 rounded bg-gray-50"
      open={defaultOpen}
    >
      <summary className="cursor-pointer px-2 py-1 text-xs font-bold hover:bg-gray-100 select-none">
        스택 trace 보기 ({trace.split('\n').length} 줄)
      </summary>
      <pre className="px-2 py-2 text-[11px] leading-snug font-mono whitespace-pre-wrap break-words overflow-x-auto max-h-96 overflow-y-auto">
        {trace}
      </pre>
    </details>
  );
}
