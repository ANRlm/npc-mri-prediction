import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity } from 'lucide-react';
import LoginForm from '@/components/auth/LoginForm';
import RegisterForm from '@/components/auth/RegisterForm';
import { useAuthStore } from '@/store/authStore';

type Tab = 'login' | 'register';

export function AuthPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [tab, setTab] = useState<Tab>('login');

  useEffect(() => {
    if (isAuthenticated) navigate('/predict', { replace: true });
  }, [isAuthenticated, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="inline-flex w-12 h-12 rounded-xl bg-fg text-bg items-center justify-center mb-5"
          >
            <Activity className="w-5 h-5" />
          </motion.div>
          <h1 className="text-2xl font-semibold tracking-tight">MRI 生存预测</h1>
          <p className="text-sm text-muted mt-2">
            鼻咽癌患者生存预后分析平台
          </p>
        </div>

        <div className="bg-card border border-border rounded-xl p-6 sm:p-8 shadow-sm">
          <div className="relative inline-flex items-center bg-bg/40 border border-border rounded-full p-0.5 mb-6">
            {(['login', 'register'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className="relative px-4 py-1.5 text-xs font-medium rounded-full"
              >
                {tab === t && (
                  <motion.span
                    layoutId="auth-tab-pill"
                    className="absolute inset-0 bg-fg rounded-full"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                  />
                )}
                <span
                  className={[
                    'relative transition-colors',
                    tab === t ? 'text-bg' : 'text-muted',
                  ].join(' ')}
                >
                  {t === 'login' ? '登录' : '注册'}
                </span>
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {tab === 'login' ? (
              <LoginForm key="login" />
            ) : (
              <RegisterForm key="register" />
            )}
          </AnimatePresence>
        </div>

        <p className="text-center text-xs text-muted mt-8">
          通过登录即表示您同意本系统的使用条款。
        </p>
      </motion.div>
    </div>
  );
}

export default AuthPage;
