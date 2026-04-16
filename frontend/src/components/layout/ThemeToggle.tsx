import { Sun, Moon, Monitor } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '@/hooks/useTheme';
import type { Theme } from '@/types';

const options: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: 'light', icon: Sun, label: '浅色' },
  { value: 'dark', icon: Moon, label: '深色' },
  { value: 'auto', icon: Monitor, label: '系统' },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="inline-flex items-center bg-card border border-border rounded-full p-0.5 relative">
      {options.map((opt) => {
        const Icon = opt.icon;
        const active = theme === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => setTheme(opt.value)}
            aria-label={opt.label}
            title={opt.label}
            className="relative h-7 w-7 flex items-center justify-center rounded-full transition-colors"
          >
            {active && (
              <motion.span
                layoutId="theme-active-pill"
                className="absolute inset-0 bg-fg/10 rounded-full"
                transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
              />
            )}
            <Icon
              className={[
                'relative w-3.5 h-3.5 transition-colors',
                active ? 'text-fg' : 'text-muted',
              ].join(' ')}
            />
          </button>
        );
      })}
    </div>
  );
}

export default ThemeToggle;
