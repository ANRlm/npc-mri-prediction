import { useEffect, useState, useCallback } from 'react';
import type { Theme } from '@/types';

const STORAGE_KEY = 'theme';

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const prefersDark =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = theme === 'dark' || (theme === 'auto' && prefersDark);
  if (isDark) root.classList.add('dark');
  else root.classList.remove('dark');
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'auto';
    return (localStorage.getItem(STORAGE_KEY) as Theme | null) || 'auto';
  });

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (theme !== 'auto') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => applyTheme('auto');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  const setTheme = useCallback((t: Theme) => setThemeState(t), []);

  return { theme, setTheme };
}
