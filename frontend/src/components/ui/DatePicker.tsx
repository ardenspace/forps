import { useState, useRef, useEffect } from 'react';
import { DayPicker } from 'react-day-picker';
import { format, parse, isValid } from 'date-fns';
import { ko } from 'date-fns/locale';
import 'react-day-picker/style.css';

interface DatePickerProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function DatePicker({
  value,
  onChange,
  disabled = false,
  placeholder = '날짜 선택',
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedDate: Date | undefined = (() => {
    if (!value) return undefined;
    const parsed = parse(value, 'yyyy-MM-dd', new Date());
    return isValid(parsed) ? parsed : undefined;
  })();

  const displayValue = selectedDate
    ? format(selectedDate, 'yyyy. M. d', { locale: ko })
    : null;

  useEffect(() => {
    if (disabled) {
      setOpen(false);
      return;
    }

    const handleMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [disabled]);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  const handleToggle = () => {
    if (!disabled) setOpen((prev) => !prev);
  };

  const handleSelect = (date: Date | undefined) => {
    if (date) {
      onChange(format(date, 'yyyy-MM-dd'));
    } else {
      onChange('');
    }
    setOpen(false);
  };

  const handleClear = () => {
    onChange('');
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={handleToggle}
        disabled={disabled}
        className={[
          'border-2 border-black w-full flex items-center justify-between',
          disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white cursor-pointer',
        ].join(' ')}
      >
        <span
          className={[
            'px-3 py-2 text-sm font-medium flex-1 text-left',
            !displayValue ? 'text-gray-400' : 'text-black',
          ].join(' ')}
        >
          {displayValue ?? placeholder}
        </span>
        <span className="px-2 py-2 border-l-2 border-black flex items-center self-stretch">
          {/* Calendar SVG icon */}
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <rect x="3" y="4" width="18" height="18" rx="0" strokeWidth={2} />
            <line x1="3" y1="9" x2="21" y2="9" strokeWidth={2} />
            <line x1="8" y1="2" x2="8" y2="6" strokeWidth={2} strokeLinecap="round" />
            <line x1="16" y1="2" x2="16" y2="6" strokeWidth={2} strokeLinecap="round" />
          </svg>
        </span>
      </button>

      {/* Calendar popup */}
      {open && (
        <div className="absolute top-full left-0 z-50 mt-0 border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(244,0,4,1)] p-3">
          <DayPicker
            mode="single"
            selected={selectedDate}
            onSelect={handleSelect}
            locale={ko}
            classNames={{
              root: 'text-black',
              months: 'flex flex-col',
              month: 'space-y-2',
              month_caption: 'flex justify-between items-center px-1 mb-2',
              caption_label: 'font-black text-sm',
              nav: 'flex items-center gap-1',
              button_previous: 'border-2 border-black p-1 hover:bg-yellow-100 transition-colors bg-white cursor-pointer',
              button_next: 'border-2 border-black p-1 hover:bg-yellow-100 transition-colors bg-white cursor-pointer',
              chevron: 'w-3 h-3 fill-black',
              month_grid: 'w-full border-collapse',
              weekdays: 'flex',
              weekday: 'text-gray-500 font-bold text-xs w-8 text-center pb-1',
              weeks: '',
              week: 'flex w-full mt-1',
              day: 'w-8 h-8 text-center text-sm p-0 relative',
              day_button: 'w-8 h-8 font-medium hover:bg-yellow-100 transition-colors flex items-center justify-center text-xs cursor-pointer',
              selected: 'bg-yellow-400 border-2 border-black font-black',
              today: 'font-black underline',
              outside: 'text-gray-400 opacity-50',
              disabled: 'text-gray-400 opacity-30 cursor-not-allowed',
            }}
          />
          {value && (
            <button
              type="button"
              onClick={handleClear}
              className="mt-2 w-full border-2 border-black text-xs font-bold py-1 hover:bg-yellow-100 transition-colors bg-white"
            >
              날짜 지우기
            </button>
          )}
        </div>
      )}
    </div>
  );
}
