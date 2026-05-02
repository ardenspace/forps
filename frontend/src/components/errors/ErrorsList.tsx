import { useState } from 'react';
import { useErrorGroups } from '@/hooks/useErrorGroups';
import type { ErrorGroupStatus, ErrorGroupSummary } from '@/types/error';

interface ErrorsListProps {
  projectId: string;
  onSelectGroup: (groupId: string) => void;
}

const STATUS_FILTER_OPTIONS: Array<{ value: ErrorGroupStatus | 'all'; label: string }> = [
  { value: 'all', label: '전체' },
  { value: 'open', label: 'OPEN' },
  { value: 'regressed', label: 'REGRESSED' },
  { value: 'resolved', label: 'RESOLVED' },
  { value: 'ignored', label: 'IGNORED' },
];

const STATUS_BADGE: Record<ErrorGroupStatus, string> = {
  open: 'bg-brand-orange/20 text-brand-coffee border-brand-orange/50',
  resolved: 'bg-brand-neon/20 text-brand-coffee border-brand-neon/50',
  ignored: 'bg-black/5 text-brand-blue border-brand-blue/20',
  regressed: 'bg-brand-orange/40 text-brand-coffee border-brand-orange',
};

function ErrorRow({
  group,
  onClick,
}: {
  group: ErrorGroupSummary;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left glass hover:bg-white/60 border-white/60 shadow-sm hover:shadow-md hover:-translate-y-0.5 rounded-xl transition-all p-3 sm:p-4"
    >
      <div className="flex items-start gap-3 flex-wrap">
        <span
          className={`px-2 py-0.5 text-[10px] font-bold uppercase border rounded-md ${
            STATUS_BADGE[group.status]
          }`}
        >
          {group.status}
        </span>
        <h4 className="font-bold text-xs sm:text-sm text-brand-blue break-words flex-1 min-w-0">
          {group.exception_class}
        </h4>
        <span className="text-[11px] text-brand-blue/70 whitespace-nowrap">
          {group.event_count.toLocaleString()} 회
        </span>
      </div>
      {group.exception_message_sample && (
        <p className="mt-2 text-[11px] text-brand-blue/80 break-words line-clamp-2">
          {group.exception_message_sample}
        </p>
      )}
      <p className="mt-2 text-[10px] text-brand-blue/60">
        최근: {new Date(group.last_seen_at).toLocaleString()}
      </p>
    </button>
  );
}

export function ErrorsList({ projectId, onSelectGroup }: ErrorsListProps) {
  const [statusFilter, setStatusFilter] = useState<ErrorGroupStatus | 'all'>('all');
  const apiStatus = statusFilter === 'all' ? undefined : statusFilter;
  const { data, isLoading, error } = useErrorGroups(projectId, { status: apiStatus, limit: 50 });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {STATUS_FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setStatusFilter(opt.value)}
            className={`px-3 py-1.5 text-[12px] sm:text-sm font-medium transition-all rounded-full ${
              statusFilter === opt.value
                ? 'bg-brand-blue text-white shadow-md'
                : 'bg-white/50 text-brand-blue hover:bg-white/60 border border-white/60 shadow-sm'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {isLoading && (
        <p className="text-muted-foreground font-medium">로딩 중...</p>
      )}
      {error && (
        <p className="text-brand-orange font-bold text-sm">에러 목록을 불러오지 못했습니다.</p>
      )}
      {data && data.items.length === 0 && (
        <div className="border-2 border-dashed border-muted-foreground rounded p-6 text-center">
          <p className="text-muted-foreground font-medium text-sm">
            {statusFilter === 'all'
              ? '아직 에러가 없습니다. 🎉'
              : `${statusFilter.toUpperCase()} 상태 에러가 없습니다.`}
          </p>
        </div>
      )}
      {data && data.items.length > 0 && (
        <>
          <p className="text-[11px] text-muted-foreground">
            {data.items.length} / 총 {data.total} 건
          </p>
          <ul className="space-y-2">
            {data.items.map((group) => (
              <li key={group.id}>
                <ErrorRow group={group} onClick={() => onSelectGroup(group.id)} />
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
