import { forwardRef, InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = '', id, ...rest }, ref) => {
    const inputId = id || rest.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-medium text-muted uppercase tracking-wide"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={[
            'h-10 px-3 rounded-md bg-card text-fg',
            'border border-border',
            'placeholder:text-muted/60',
            'focus:border-accent focus:ring-1 focus:ring-accent',
            'transition-colors',
            error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : '',
            className,
          ].join(' ')}
          {...rest}
        />
        {hint && !error && <p className="text-xs text-muted">{hint}</p>}
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

export default Input;
