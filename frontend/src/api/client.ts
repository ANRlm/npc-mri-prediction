import axios, { AxiosError } from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Let authStore.fetchUser handle state update; only redirect if not already on /
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      }
    }
    return Promise.reject(err);
  }
);

export default api;

export async function downloadFile(filename: string): Promise<void> {
  const token = localStorage.getItem('token');
  const res = await fetch(`/files/${encodeURIComponent(filename)}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
