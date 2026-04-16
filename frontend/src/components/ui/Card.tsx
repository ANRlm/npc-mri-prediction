import { HTMLAttributes, forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  noPadding?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className = '', noPadding = false, ...rest }, ref) => {
    return (
      <div
        ref={ref}
        className={[
          'bg-card border border-border rounded-lg',
          noPadding ? '' : 'p-6',
          className,
        ].join(' ')}
        {...rest}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

interface MotionCardProps extends HTMLMotionProps<'div'> {
  noPadding?: boolean;
}

export const MotionCard = ({
  children,
  className = '',
  noPadding = false,
  ...rest
}: MotionCardProps) => {
  return (
    <motion.div
      className={[
        'bg-card border border-border rounded-lg',
        noPadding ? '' : 'p-6',
        className,
      ].join(' ')}
      {...rest}
    >
      {children}
    </motion.div>
  );
};

export default Card;
