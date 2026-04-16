import { FormEvent, useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Search, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import api from '@/api/client';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import HistoryTable from '@/components/history/HistoryTable';
import type { PredictionData } from '@/types';

const PAGE_SIZE = 20;

const TIME_RANGE_OPTIONS = [
  { value: '', label: '全部时间' },
  { value: 'week', label: '最近一周' },
  { value: 'month', label: '最近一月' },
  { value: 'year', label: '最近一年' },
];

export function HistoryPage() {
  const [patientId, setPatientId] = useState('');
  const [search, setSearch] = useState('');
  const [timeRange, setTimeRange] = useState('');
  const [page, setPage] = useState(0);
  const [rows, setRows] = useState<PredictionData[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        limit: PAGE_SIZE,
        skip: page * PAGE_SIZE,
      };
      if (search.trim()) params.patient_id = search.trim();
      if (timeRange) params.time_range = timeRange;
      const res = await api.get('/prediction-history', { params });
      if (res.data.success) {
        setRows(res.data.data || []);
        setTotal(res.data.count || 0);
      } else {
        setError(res.data.message || '获取历史记录失败');
      }
    } catch (e: any) {
      setError(e?.response?.data?.message || '获取历史记录失败');
    } finally {
      setLoading(false);
    }
  }, [search, timeRange, page]);

  useEffect(() => {
    void fetchHistory();
  }, [fetchHistory]);

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    setPage(0);
    setSearch(patientId);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/prediction/${id}`);
      setRows((prev) => prev.filter((r) => r.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (e: any) {
      setError(e?.response?.data?.message || '删除失败');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-semibold tracking-tight">预测历史</h1>
        <p className="text-sm text-muted mt-2">查看历史预测记录，支持按患者编号和时间范围筛选。</p>
      </motion.div>

      <form
        onSubmit={handleSearch}
        className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3 mb-6"
      >
        <div className="flex-1 max-w-sm">
          <Input
            label="患者编号"
            placeholder="输入患者编号筛选"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-fg/80">时间范围</label>
          <select
            value={timeRange}
            onChange={(e) => { setTimeRange(e.target.value); setPage(0); }}
            className="text-sm bg-card border border-border rounded-lg px-3 py-2 text-fg focus:outline-none focus:ring-1 focus:ring-accent h-[38px]"
          >
            {TIME_RANGE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <Button type="submit" variant="secondary">
          <Search className="w-4 h-4" /> 搜索
        </Button>
        {(search || timeRange) && (
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              setPatientId('');
              setSearch('');
              setTimeRange('');
              setPage(0);
            }}
          >
            清除
          </Button>
        )}
      </form>

      {error && (
        <p className="text-xs text-red-500 mb-4">{error}</p>
      )}

      {loading ? (
        <div className="border border-border rounded-lg py-16 flex items-center justify-center text-sm text-muted">
          <Loader2 className="w-4 h-4 animate-spin mr-2" /> 加载中…
        </div>
      ) : (
        <HistoryTable rows={rows} onDelete={handleDelete} />
      )}

      <div className="flex items-center justify-between mt-6">
        <p className="text-xs text-muted">
          共 {total} 条记录 · 第 {page + 1} / {totalPages} 页
        </p>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={page === 0 || loading}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            <ChevronLeft className="w-3.5 h-3.5" /> 上一页
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={page >= totalPages - 1 || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页 <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </main>
  );
}

export default HistoryPage;
