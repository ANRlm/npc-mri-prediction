import { forwardRef, ReactNode } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'ref' | 'children'> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  fullWidth?: boolean;
  children?: ReactNode;
}

const variantStyles: Record<Variant, string> = {
  primary:
    'bg-fg text-bg hover:opacity-90 disabled:opacity-50',
  secondary:
    'bg-card text-fg border border-border hover:bg-border/30 disabled:opacity-50',
  ghost:
    'bg-transparent text-fg hover:bg-border/30 disabled:opacity-50',
  danger:
    'bg-red-600 text-white hover:bg-red-700 disabled:opacity-50',
};

const sizeStyles: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      fullWidth = false,
      disabled,
      children,
      className = '',
      ...rest
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        whileTap={{ scale: 0.97 }}
        disabled={disabled || loading}
        className={[
          'inline-flex items-center justify-center gap-2 rounded-md font-medium',
          'transition-colors duration-150',
          variantStyles[variant],
          sizeStyles[size],
          fullWidth ? 'w-full' : '',
          className,
        ].join(' ')}
        {...rest}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </motion.button>
    );
  }
);
Button.displayName = 'Button';

export default Button;
