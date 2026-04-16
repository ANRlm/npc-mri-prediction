import { Component, ReactNode, useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import Header from '@/components/layout/Header';
import AuthPage from '@/pages/AuthPage';
import PredictionPage from '@/pages/PredictionPage';
import HistoryPage from '@/pages/HistoryPage';
import FilesPage from '@/pages/FilesPage';
import MriViewerPage from '@/pages/MriViewerPage';
import { useAuthStore } from '@/store/authStore';
import { useTheme } from '@/hooks/useTheme';

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
          <p className="text-sm font-medium mb-2">页面加载出错</p>
          <p className="text-xs text-muted mb-4">{(this.state.error as Error).message}</p>
          <button
            className="text-xs underline text-muted"
            onClick={() => this.setState({ error: null })}
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function PageWrapper({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  // ensure theme hook is mounted at root
  useTheme();
  const location = useLocation();
  const hydrate = useAuthStore((s) => s.hydrate);
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (isAuthenticated) void fetchUser();
  }, [isAuthenticated, fetchUser]);

  return (
    <div className="min-h-screen flex flex-col bg-bg text-fg">
      <Header />
      <ErrorBoundary>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route
            path="/"
            element={
              <PageWrapper>
                <AuthPage />
              </PageWrapper>
            }
          />
          <Route
            path="/predict"
            element={
              <ProtectedRoute>
                <PageWrapper>
                  <PredictionPage />
                </PageWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <PageWrapper>
                  <HistoryPage />
                </PageWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/files"
            element={
              <ProtectedRoute>
                <PageWrapper>
                  <FilesPage />
                </PageWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/mri-viewer"
            element={
              <ProtectedRoute>
                <PageWrapper>
                  <MriViewerPage />
                </PageWrapper>
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
      </ErrorBoundary>
    </div>
  );
}
