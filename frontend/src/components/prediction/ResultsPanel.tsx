import { motion, AnimatePresence } from 'framer-motion';
import { Download, Activity, TrendingUp, ShieldCheck } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import SurvivalChart from '@/components/charts/SurvivalChart';
import { usePredictionStore } from '@/store/predictionStore';

const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

export function ResultsPanel() {
  const { currentPrediction, survivalData, isLoading } = usePredictionStore();

  const handleExport = () => {
    if (!currentPrediction) return;
    const blob = new Blob([JSON.stringify(currentPrediction, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `prediction_${currentPrediction.patient_id}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!currentPrediction && !isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="border border-dashed border-border rounded-lg h-full min-h-[400px] flex flex-col items-center justify-center text-center px-6"
      >
        <div className="w-12 h-12 rounded-full border border-border flex items-center justify-center mb-4 text-muted">
          <Activity className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-medium">暂无预测结果</h3>
        <p className="text-xs text-muted mt-1.5 max-w-xs">
          填写左侧患者参数并提交，结果将在此处呈现。
        </p>
      </motion.div>
    );
  }

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="border border-border rounded-lg h-full min-h-[400px] flex flex-col items-center justify-center text-center px-6"
      >
        <div className="w-10 h-10 rounded-full border-2 border-border border-t-fg animate-spin" />
        <p className="text-xs text-muted mt-4">正在计算预测结果…</p>
      </motion.div>
    );
  }

  if (!currentPrediction) return null;
  const isHighRisk = currentPrediction.risk_group === '高风险组';

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={currentPrediction.timestamp}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="flex flex-col gap-5"
      >
        {/* Header */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.05 }}
          className="bg-card border border-border rounded-lg p-6"
        >
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs text-muted uppercase tracking-wide">患者编号</p>
              <p className="text-lg font-semibold mt-1">{currentPrediction.patient_id}</p>
              <p className="text-xs text-muted mt-1">
                {new Date(currentPrediction.timestamp).toLocaleString('zh-CN')}
              </p>
            </div>
            <div className="flex flex-col items-end">
              <Badge variant={isHighRisk ? 'danger' : 'success'} className="mb-2">
                {currentPrediction.risk_group}
              </Badge>
              <p className="text-xs text-muted">风险评分</p>
              <p className="text-3xl font-semibold tracking-tight">
                {currentPrediction.risk_score.toFixed(3)}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Survival rates */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.12 }}
          className="grid grid-cols-3 gap-3"
        >
          {(['1年生存率', '3年生存率', '5年生存率'] as const).map((k, i) => (
            <motion.div
              key={k}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
              className="bg-card border border-border rounded-lg p-4"
            >
              <p className="text-xs text-muted">{k}</p>
              <p className="text-2xl font-semibold mt-1.5 tracking-tight">
                {currentPrediction.survival_rates[k]}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* Metrics */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.2 }}
          className="bg-card border border-border rounded-lg p-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-muted" />
            <h3 className="text-sm font-medium">模型指标</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {(
              [
                ['C-Index', currentPrediction.metrics.c_index],
                ['AUC', currentPrediction.metrics.auc],
                ['Sensitivity', currentPrediction.metrics.sensitivity],
                ['Specificity', currentPrediction.metrics.specificity],
              ] as const
            ).map(([label, val]) => (
              <div key={label}>
                <p className="text-xs text-muted">{label}</p>
                <p className="text-lg font-medium mt-1 tabular-nums">
                  {typeof val === 'number' ? val.toFixed(3) : '—'}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Survival chart */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.25 }}
          className="bg-card border border-border rounded-lg p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-muted" />
              <h3 className="text-sm font-medium">生存曲线</h3>
            </div>
            <p className="text-xs text-muted">60 个月预测</p>
          </div>
          {currentPrediction.survival_curve_base64 ? (
            <img
              src={`data:image/png;base64,${currentPrediction.survival_curve_base64}`}
              alt="生存曲线"
              className="w-full rounded-md"
            />
          ) : (
            <SurvivalChart data={survivalData} />
          )}
        </motion.div>

        {/* Clinical advice */}
        {currentPrediction.clinical_advice && currentPrediction.clinical_advice.length > 0 && (
          <motion.div
            {...fadeUp}
            transition={{ delay: 0.3 }}
            className="bg-card border border-border rounded-lg p-6"
          >
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-muted" />
              <h3 className="text-sm font-medium">临床建议</h3>
            </div>
            <ul className="space-y-2.5">
              {currentPrediction.clinical_advice.map((advice, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.35 + i * 0.04 }}
                  className="flex gap-3 text-sm leading-relaxed"
                >
                  <span className="text-muted mt-1">·</span>
                  <span className="text-fg/90">{advice}</span>
                </motion.li>
              ))}
            </ul>
          </motion.div>
        )}

        {/* Actions */}
        <motion.div
          {...fadeUp}
          transition={{ delay: 0.35 }}
          className="flex items-center gap-3"
        >
          <Button variant="secondary" onClick={handleExport}>
            <Download className="w-4 h-4" /> 导出结果
          </Button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default ResultsPanel;
