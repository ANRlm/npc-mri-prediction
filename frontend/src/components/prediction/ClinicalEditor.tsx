import { useState } from 'react';
import { motion } from 'framer-motion';
import { HelpCircle } from 'lucide-react';

export interface ClinicalData {
  patient_id: string;
  sex: string;
  age: string;
  t_stage: string;
  n_stage: string;
  total_stage: string;
  dna_before: string;
  dna_after: string;
}

export const DEFAULT_CLINICAL: ClinicalData = {
  patient_id: 'PT-001',
  sex: '男',
  age: '52',
  t_stage: '3',
  n_stage: '2',
  total_stage: '3',
  dna_before: '2.50',
  dna_after: '1.35',
};

const FIELD_META: {
  key: keyof ClinicalData;
  label: string;
  tip: string;
  type: 'text' | 'select' | 'number';
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}[] = [
  {
    key: 'patient_id',
    label: '患者编号',
    tip: '用于标识本次预测记录，可自定义，如 PT-001',
    type: 'text',
  },
  {
    key: 'sex',
    label: '性别',
    tip: '患者生理性别',
    type: 'select',
    options: [
      { value: '男', label: '男' },
      { value: '女', label: '女' },
    ],
  },
  {
    key: 'age',
    label: '年龄',
    tip: '患者确诊时年龄（岁），范围 1–120',
    type: 'number',
    min: 1,
    max: 120,
    step: 1,
  },
  {
    key: 't_stage',
    label: 'T 分期',
    tip: '原发肿瘤 T 分期（AJCC 第8版）：T1=1，T2=2，T3=3，T4=4',
    type: 'select',
    options: [
      { value: '1', label: 'T1' },
      { value: '2', label: 'T2' },
      { value: '3', label: 'T3' },
      { value: '4', label: 'T4' },
    ],
  },
  {
    key: 'n_stage',
    label: 'N 分期',
    tip: '区域淋巴结 N 分期（AJCC 第8版）：N0=0，N1=1，N2=2，N3=3',
    type: 'select',
    options: [
      { value: '0', label: 'N0' },
      { value: '1', label: 'N1' },
      { value: '2', label: 'N2' },
      { value: '3', label: 'N3' },
    ],
  },
  {
    key: 'total_stage',
    label: '总分期',
    tip: '肿瘤总分期（AJCC 第8版）：I=1，II=2，III=3，IV=4',
    type: 'select',
    options: [
      { value: '1', label: 'I 期' },
      { value: '2', label: 'II 期' },
      { value: '3', label: 'III 期' },
      { value: '4', label: 'IV 期' },
    ],
  },
  {
    key: 'dna_before',
    label: '治疗前 EBV DNA',
    tip: '放化疗开始前检测的 EBV DNA 拷贝数（copies/mL）',
    type: 'number',
    min: 0,
    step: 0.01,
  },
  {
    key: 'dna_after',
    label: '治疗后 EBV DNA',
    tip: '放化疗结束后检测的 EBV DNA 拷贝数（copies/mL），0 表示转阴',
    type: 'number',
    min: 0,
    step: 0.01,
  },
];

interface ClinicalEditorProps {
  value: ClinicalData;
  onChange: (data: ClinicalData) => void;
}

export function ClinicalEditor({ value, onChange }: ClinicalEditorProps) {
  const [activeTooltip, setActiveTooltip] = useState<keyof ClinicalData | null>(null);

  const handleChange = (key: keyof ClinicalData, val: string) => {
    onChange({ ...value, [key]: val });
  };

  return (
    <div className="flex flex-col gap-3">
      {FIELD_META.map((field) => (
        <div key={field.key} className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <label className="text-xs font-medium text-fg/80">{field.label}</label>
            <button
              type="button"
              className="text-muted hover:text-fg transition-colors"
              onMouseEnter={() => setActiveTooltip(field.key)}
              onMouseLeave={() => setActiveTooltip(null)}
            >
              <HelpCircle className="w-3 h-3" />
            </button>
          </div>

          {activeTooltip === field.key && (
            <motion.p
              initial={{ opacity: 0, y: -2 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs text-muted bg-card border border-border rounded-md px-2.5 py-1.5 -mt-0.5"
            >
              {field.tip}
            </motion.p>
          )}

          {field.type === 'select' ? (
            <select
              value={value[field.key]}
              onChange={(e) => handleChange(field.key, e.target.value)}
              className="w-full text-sm bg-card border border-border rounded-lg px-3 py-2 text-fg focus:outline-none focus:ring-1 focus:ring-accent"
            >
              {field.options!.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={field.type}
              value={value[field.key]}
              min={field.min}
              max={field.max}
              step={field.step}
              onChange={(e) => handleChange(field.key, e.target.value)}
              className="w-full text-sm bg-card border border-border rounded-lg px-3 py-2 text-fg focus:outline-none focus:ring-1 focus:ring-accent"
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default ClinicalEditor;
