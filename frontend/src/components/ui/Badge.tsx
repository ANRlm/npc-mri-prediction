import { HTMLAttributes } from 'react';

type Variant = 'default' | 'success' | 'warning' | 'danger' | 'info';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const styles: Record<Variant, string> = {
  default:
    'bg-border/40 text-fg border border-border',
  success:
    'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20',
  warning:
    'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
  danger:
    'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20',
  info:
    'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20',
};

export function Badge({
  variant = 'default',
  className = '',
  children,
  ...rest
}: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
        styles[variant],
        className,
      ].join(' ')}
      {...rest}
    >
      {children}
    </span>
  );
}

export default Badge;
