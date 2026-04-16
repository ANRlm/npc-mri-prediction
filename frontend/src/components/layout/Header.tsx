import { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogOut, Activity } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { useAuthStore } from '@/store/authStore';

const navItems = [
  { to: '/predict', label: '预测' },
  { to: '/history', label: '历史' },
  { to: '/mri-viewer', label: '影像' },
  { to: '/files', label: '文件' },
];

export function Header() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 4);
    handler();
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={[
        'sticky top-0 z-40 w-full transition-all',
        scrolled
          ? 'backdrop-blur-md bg-bg/70 border-b border-border'
          : 'bg-transparent border-b border-transparent',
      ].join(' ')}
    >
      <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <NavLink to={isAuthenticated ? '/predict' : '/'} className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-fg text-bg flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
            <span className="font-semibold text-sm tracking-tight">MRI Predictor</span>
          </NavLink>
          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      'px-3 py-1.5 rounded-md text-sm transition-colors relative',
                      isActive
                        ? 'text-fg'
                        : 'text-muted hover:text-fg',
                    ].join(' ')
                  }
                >
                  {({ isActive }) => (
                    <>
                      {item.label}
                      {isActive && (
                        <motion.span
                          layoutId="nav-underline"
                          className="absolute left-2 right-2 -bottom-px h-px bg-fg"
                        />
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>
          )}
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          {isAuthenticated && user && (
            <>
              <div className="hidden sm:flex items-center text-xs text-muted">
                <span className="font-medium text-fg">{user.username}</span>
              </div>
              <button
                onClick={handleLogout}
                aria-label="登出"
                className="h-8 w-8 flex items-center justify-center rounded-full border border-border text-muted hover:text-fg hover:border-fg/40 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>

      {isAuthenticated && (
        <nav className="md:hidden border-t border-border flex items-center justify-around py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  'px-3 py-1 rounded-md text-xs',
                  isActive ? 'text-fg font-medium' : 'text-muted',
                ].join(' ')
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      )}
    </motion.header>
  );
}

export default Header;
