import { create } from 'zustand';
import api from '@/api/client';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (
    username: string,
    email: string,
    password: string,
    code: string
  ) => Promise<boolean>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  hydrate: () => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as User;
        set({ user, token, isAuthenticated: true });
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  },

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.post('/login', { username, password });
      const data = res.data;
      if (data.success && data.token) {
        const user: User = { username: data.username, email: data.email };
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(user));
        set({ user, token: data.token, isAuthenticated: true, isLoading: false });
        return true;
      }
      set({ error: data.message || '登录失败', isLoading: false });
      return false;
    } catch (e: any) {
      const msg = e?.response?.data?.message || '登录失败，请稍后重试';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  register: async (username, email, password, code) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.post('/register', { username, email, password, code });
      const data = res.data;
      if (data.success) {
        set({ isLoading: false });
        return await get().login(username, password);
      }
      set({ error: data.message || '注册失败', isLoading: false });
      return false;
    } catch (e: any) {
      const msg = e?.response?.data?.message || '注册失败，请稍后重试';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  logout: async () => {
    try {
      await api.post('/logout');
    } catch {
      // ignore
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ user: null, token: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const res = await api.get('/user');
      if (res.data.success) {
        const user: User = {
          username: res.data.username,
          email: res.data.email,
          created_at: res.data.created_at,
        };
        localStorage.setItem('user', JSON.stringify(user));
        set({ user, isAuthenticated: true });
      }
    } catch (e: any) {
      if (e?.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        set({ user: null, token: null, isAuthenticated: false });
      }
    }
  },
}));
