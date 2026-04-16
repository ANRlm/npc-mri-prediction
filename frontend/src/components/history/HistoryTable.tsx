import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Trash2 } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import type { PredictionData } from '@/types';

interface Props {
  rows: PredictionData[];
  onDelete?: (id: string) => void;
}

export function HistoryTable({ rows, onDelete }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  if (rows.length === 0) {
    return (
      <div className="border border-dashed border-border rounded-lg py-16 text-center text-sm text-muted">
        暂无历史记录
      </div>
    );
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!onDelete) return;
    setDeletingId(id);
    await onDelete(id);
    setDeletingId(null);
  };

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="hidden md:grid grid-cols-[140px_1fr_120px_100px_repeat(3,1fr)_40px_40px] items-center gap-3 px-4 py-3 bg-card border-b border-border text-xs uppercase tracking-wide text-muted">
        <span>日期</span>
        <span>患者编号</span>
        <span>风险分组</span>
        <span>风险评分</span>
        <span>1 年</span>
        <span>3 年</span>
        <span>5 年</span>
        <span></span>
        <span></span>
      </div>
      <ul>
        <AnimatePresence initial={false}>
          {rows.map((row, idx) => {
            const expanded = expandedIdx === idx;
            const isHigh = row.risk_group === '高风险组';
            return (
              <motion.li
                key={`${row.patient_id}-${row.timestamp}-${idx}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2, delay: idx * 0.02 }}
                className="border-b border-border last:border-b-0"
              >
                <div className="w-full grid grid-cols-2 md:grid-cols-[140px_1fr_120px_100px_repeat(3,1fr)_40px_40px] items-center gap-3 px-4 py-4">
                  <button
                    type="button"
                    onClick={() => setExpandedIdx(expanded ? null : idx)}
                    className="col-span-2 md:col-span-8 grid grid-cols-2 md:grid-cols-[140px_1fr_120px_100px_repeat(3,1fr)_40px] items-center gap-3 text-left hover:bg-border/20 transition-colors rounded-md -mx-1 px-1"
                  >
                    <span className="text-xs text-muted md:order-none order-2">
                      {new Date(row.timestamp).toLocaleString('zh-CN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="font-medium text-sm md:order-none order-1">{row.patient_id}</span>
                    <span className="md:order-none order-3">
                      <Badge variant={isHigh ? 'danger' : 'success'}>{row.risk_group}</Badge>
                    </span>
                    <span className="text-sm tabular-nums md:order-none order-4">
                      {typeof row.risk_score === 'number' ? row.risk_score.toFixed(3) : '—'}
                    </span>
                    <span className="text-sm tabular-nums hidden md:inline">
                      {row.survival_rates?.['1年生存率'] ?? '—'}
                    </span>
                    <span className="text-sm tabular-nums hidden md:inline">
                      {row.survival_rates?.['3年生存率'] ?? '—'}
                    </span>
                    <span className="text-sm tabular-nums hidden md:inline">
                      {row.survival_rates?.['5年生存率'] ?? '—'}
                    </span>
                    <ChevronDown
                      className={[
                        'w-4 h-4 text-muted transition-transform hidden md:block',
                        expanded ? 'rotate-180' : '',
                      ].join(' ')}
                    />
                  </button>
                  {onDelete && row.id ? (
                    <button
                      type="button"
                      disabled={deletingId === row.id}
                      onClick={(e) => handleDelete(e, row.id!)}
                      className="hidden md:flex items-center justify-center w-7 h-7 rounded-md text-muted hover:text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-40"
                      title="删除记录"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <span className="hidden md:block" />
                  )}
                </div>

                <AnimatePresence initial={false}>
                  {expanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="overflow-hidden bg-bg/40"
                    >
                      <div className="px-4 py-5 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h4 className="text-xs uppercase tracking-wide text-muted mb-3">
                            模型指标
                          </h4>
                          <dl className="grid grid-cols-2 gap-3 text-sm">
                            <Stat label="C-Index" value={row.metrics?.c_index} />
                            <Stat label="AUC" value={row.metrics?.auc} />
                            <Stat label="Sensitivity" value={row.metrics?.sensitivity} />
                            <Stat label="Specificity" value={row.metrics?.specificity} />
                          </dl>
                        </div>
                        <div>
                          <h4 className="text-xs uppercase tracking-wide text-muted mb-3">
                            临床建议
                          </h4>
                          {row.clinical_advice && row.clinical_advice.length > 0 ? (
                            <ul className="space-y-1.5 text-sm">
                              {row.clinical_advice.map((a, i) => (
                                <li key={i} className="flex gap-2">
                                  <span className="text-muted">·</span>
                                  <span className="text-fg/90">{a}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-xs text-muted">无</p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.li>
            );
          })}
        </AnimatePresence>
      </ul>
    </div>
  );
}

function Stat({ label, value }: { label: string; value?: number }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="font-medium tabular-nums">
        {typeof value === 'number' ? value.toFixed(3) : '—'}
      </dd>
    </div>
  );
}

export default HistoryTable;
