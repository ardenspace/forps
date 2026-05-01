import type { LogLevel } from '@/types/log';

interface LogLevelBadgeProps {
  level: LogLevel;
  className?: string;
}

const LEVEL_STYLES: Record<LogLevel, string> = {
  DEBUG: 'bg-gray-100 text-gray-700 border-gray-400',
  INFO: 'bg-blue-100 text-blue-800 border-blue-400',
  WARNING: 'bg-yellow-100 text-yellow-800 border-yellow-500',
  ERROR: 'bg-red-100 text-red-800 border-red-500',
  CRITICAL: 'bg-purple-100 text-purple-800 border-purple-500',
};

export function LogLevelBadge({ level, className = '' }: LogLevelBadgeProps) {
  const style = LEVEL_STYLES[level];
  return (
    <span
      className={`inline-block px-1.5 py-0.5 text-[10px] font-bold uppercase border-2 rounded ${style} ${className}`}
    >
      {level}
    </span>
  );
}
