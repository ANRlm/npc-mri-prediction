import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import type { SurvivalCurveData } from '@/types';

interface Props {
  data: SurvivalCurveData | null;
  loading?: boolean;
}

interface ChartPoint {
  month: number;
  patient: number;
  low_risk: number;
  high_risk: number;
}

export function SurvivalChart({ data, loading }: Props) {
  const chartData = useMemo<ChartPoint[]>(() => {
    if (!data) return [];
    const { months, survival_curves } = data;
    return months.map((m, i) => ({
      month: m,
      patient: Number((survival_curves.patient[i] ?? 0).toFixed(4)),
      low_risk: Number((survival_curves.low_risk[i] ?? 0).toFixed(4)),
      high_risk: Number((survival_curves.high_risk[i] ?? 0).toFixed(4)),
    }));
  }, [data]);

  if (loading) {
    return (
      <div className="h-72 flex items-center justify-center text-xs text-muted">
        正在加载生存曲线…
      </div>
    );
  }

  if (!data || chartData.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-xs text-muted border border-dashed border-border rounded-md">
        暂无生存曲线数据
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: -8 }}>
          <CartesianGrid stroke="rgb(var(--color-border))" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 11, fill: 'rgb(var(--color-muted))' }}
            stroke="rgb(var(--color-border))"
            label={{
              value: '月份',
              position: 'insideBottom',
              offset: -2,
              style: { fontSize: 11, fill: 'rgb(var(--color-muted))' },
            }}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v) => `${Math.round(v * 100)}%`}
            tick={{ fontSize: 11, fill: 'rgb(var(--color-muted))' }}
            stroke="rgb(var(--color-border))"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgb(var(--color-card))',
              border: '1px solid rgb(var(--color-border))',
              borderRadius: 8,
              fontSize: 12,
              color: 'rgb(var(--color-fg))',
            }}
            labelFormatter={(label) => `第 ${label} 月`}
            formatter={(value: number, name) => {
              const labels: Record<string, string> = {
                patient: '患者',
                low_risk: '低风险组',
                high_risk: '高风险组',
              };
              return [`${(value * 100).toFixed(1)}%`, labels[name as string] || name];
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: 'rgb(var(--color-muted))' }}
            formatter={(value) => {
              const labels: Record<string, string> = {
                patient: '患者',
                low_risk: '低风险组',
                high_risk: '高风险组',
              };
              return labels[value] || value;
            }}
          />
          <Line
            type="monotone"
            dataKey="patient"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            isAnimationActive
            animationDuration={800}
          />
          <Line
            type="monotone"
            dataKey="low_risk"
            stroke="#10b981"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
            isAnimationActive
            animationDuration={800}
          />
          <Line
            type="monotone"
            dataKey="high_risk"
            stroke="#ef4444"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
            isAnimationActive
            animationDuration={800}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default SurvivalChart;
