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
  open: 'bg-red-100 text-red-800 border-red-500',
  resolved: 'bg-green-100 text-green-800 border-green-500',
  ignored: 'bg-gray-100 text-gray-700 border-gray-500',
  regressed: 'bg-orange-100 text-orange-800 border-orange-500',
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
      className="w-full text-left bg-white border-2 border-black shadow-[2px_2px_0px_0px_rgba(244,0,4,1)] hover:shadow-[4px_4px_0px_0px_rgba(244,0,4,1)] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all p-2.5 sm:p-3"
    >
      <div className="flex items-start gap-2 flex-wrap">
        <span
          className={`px-1.5 py-0.5 text-[10px] font-bold uppercase border-2 rounded ${
            STATUS_BADGE[group.status]
          }`}
        >
          {group.status}
        </span>
        <h4 className="font-bold text-xs sm:text-sm break-words flex-1 min-w-0">
          {group.exception_class}
        </h4>
        <span className="text-[11px] text-muted-foreground whitespace-nowrap">
          {group.event_count.toLocaleString()} 회
        </span>
      </div>
      {group.exception_message_sample && (
        <p className="mt-1 text-[11px] text-muted-foreground break-words line-clamp-2">
          {group.exception_message_sample}
        </p>
      )}
      <p className="mt-1 text-[10px] text-muted-foreground">
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
            className={`px-2.5 py-1 text-xs font-bold border-2 border-black rounded transition-colors ${
              statusFilter === opt.value
                ? 'bg-black text-white'
                : 'bg-background hover:bg-yellow-100'
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
        <p className="text-red-700 font-bold text-sm">에러 목록을 불러오지 못했습니다.</p>
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
