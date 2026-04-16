import { forwardRef, SelectHTMLAttributes } from 'react';
import { ChevronDown } from 'lucide-react';

interface Option {
  value: string | number;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: Option[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, className = '', id, ...rest }, ref) => {
    const selectId = id || rest.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="text-xs font-medium text-muted uppercase tracking-wide"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={[
              'w-full h-10 pl-3 pr-9 rounded-md bg-card text-fg appearance-none',
              'border border-border',
              'focus:border-accent focus:ring-1 focus:ring-accent',
              'transition-colors',
              error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : '',
              className,
            ].join(' ')}
            {...rest}
          >
            {options.map((opt) => (
              <option key={String(opt.value)} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
        </div>
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);
Select.displayName = 'Select';

export default Select;
