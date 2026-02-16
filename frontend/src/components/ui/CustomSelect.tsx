import { useState, useEffect, useRef } from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function CustomSelect({
  value,
  onChange,
  options,
  placeholder = '선택',
  disabled = false,
  className = '',
}: CustomSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedLabel = options.find((o) => o.value === value)?.label ?? null;

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

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
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
            !selectedLabel ? 'text-gray-400' : 'text-black',
          ].join(' ')}
        >
          {selectedLabel ?? placeholder}
        </span>
        <span className="px-2 py-2 border-l-2 border-black flex items-center self-stretch">
          <svg
            className={`w-3 h-3 transition-transform duration-150 ${open ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {/* Dropdown list */}
      {open && (
        <ul
          role="listbox"
          className="absolute top-full left-0 right-0 z-50 mt-0 border-2 border-black border-t-0 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto"
        >
          {options.map((option) => (
            <li
              key={option.value}
              role="option"
              aria-selected={option.value === value}
              onClick={() => handleSelect(option.value)}
              className={[
                'px-3 py-2 text-sm cursor-pointer font-medium',
                option.value === value
                  ? 'bg-yellow-400 font-bold'
                  : 'hover:bg-yellow-50',
              ].join(' ')}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
