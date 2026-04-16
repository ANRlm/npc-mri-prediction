import { FormEvent, useState } from 'react';
import { motion } from 'framer-motion';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import type { PredictionRequest } from '@/types';
import { usePredictionStore } from '@/store/predictionStore';

const sexOptions = [
  { value: '男', label: '男' },
  { value: '女', label: '女' },
];
const tStageOptions = [1, 2, 3, 4].map((v) => ({ value: v, label: `T${v}` }));
const nStageOptions = [0, 1, 2, 3].map((v) => ({ value: v, label: `N${v}` }));
const totalStageOptions = [
  { value: 1, label: 'Ⅰ期' },
  { value: 2, label: 'Ⅱ期' },
  { value: 3, label: 'Ⅲ期' },
  { value: 4, label: 'Ⅳ期' },
];

interface FormState {
  Patient_ID: string;
  性别: string;
  年龄: string;
  T分期: string;
  N分期: string;
  总分期: string;
  治疗前DNA: string;
  治疗后DNA: string;
}

const initial: FormState = {
  Patient_ID: '',
  性别: '男',
  年龄: '',
  T分期: '1',
  N分期: '0',
  总分期: '1',
  治疗前DNA: '',
  治疗后DNA: '',
};

export function PredictionForm() {
  const { predict, fetchSurvivalData, isLoading, error } = usePredictionStore();
  const [form, setForm] = useState<FormState>(initial);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  const validate = (): boolean => {
    const e: Partial<Record<keyof FormState, string>> = {};
    if (!form.Patient_ID.trim()) e.Patient_ID = '请输入患者编号';
    const age = Number(form.年龄);
    if (!form.年龄 || Number.isNaN(age) || age < 1 || age > 150) e.年龄 = '年龄须在 1-150 之间';
    const pre = Number(form.治疗前DNA);
    if (!form.治疗前DNA || Number.isNaN(pre) || pre <= 0) e.治疗前DNA = '须为正数';
    const post = Number(form.治疗后DNA);
    if (!form.治疗后DNA || Number.isNaN(post) || post <= 0) e.治疗后DNA = '须为正数';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    const payload: PredictionRequest = {
      Patient_ID: form.Patient_ID.trim(),
      性别: form.性别,
      年龄: Number(form.年龄),
      T分期: Number(form.T分期),
      N分期: Number(form.N分期),
      总分期: Number(form.总分期),
      治疗前DNA: Number(form.治疗前DNA),
      治疗后DNA: Number(form.治疗后DNA),
    };
    const ok = await predict(payload);
    if (ok) {
      void fetchSurvivalData(payload);
    }
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col gap-5"
    >
      <div>
        <h2 className="text-lg font-semibold tracking-tight">患者参数</h2>
        <p className="text-xs text-muted mt-1">输入患者临床数据以生成生存预测</p>
      </div>

      <Input
        label="患者编号"
        name="Patient_ID"
        placeholder="例如 PT-00123"
        value={form.Patient_ID}
        onChange={(e) => update('Patient_ID', e.target.value)}
        error={errors.Patient_ID}
      />

      <div className="grid grid-cols-2 gap-4">
        <Select
          label="性别"
          name="sex"
          options={sexOptions}
          value={form.性别}
          onChange={(e) => update('性别', e.target.value)}
        />
        <Input
          label="年龄"
          name="age"
          type="number"
          min={1}
          max={150}
          placeholder="岁"
          value={form.年龄}
          onChange={(e) => update('年龄', e.target.value)}
          error={errors.年龄}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Select
          label="T 分期"
          name="t_stage"
          options={tStageOptions}
          value={form.T分期}
          onChange={(e) => update('T分期', e.target.value)}
        />
        <Select
          label="N 分期"
          name="n_stage"
          options={nStageOptions}
          value={form.N分期}
          onChange={(e) => update('N分期', e.target.value)}
        />
        <Select
          label="总分期"
          name="total_stage"
          options={totalStageOptions}
          value={form.总分期}
          onChange={(e) => update('总分期', e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="治疗前 DNA"
          name="pre_dna"
          type="number"
          step="any"
          min={0}
          placeholder="copies/mL"
          value={form.治疗前DNA}
          onChange={(e) => update('治疗前DNA', e.target.value)}
          error={errors.治疗前DNA}
        />
        <Input
          label="治疗后 DNA"
          name="post_dna"
          type="number"
          step="any"
          min={0}
          placeholder="copies/mL"
          value={form.治疗后DNA}
          onChange={(e) => update('治疗后DNA', e.target.value)}
          error={errors.治疗后DNA}
        />
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-red-500"
        >
          {error}
        </motion.p>
      )}

      <Button type="submit" loading={isLoading} size="lg" fullWidth>
        {isLoading ? '正在预测' : '生成预测'}
      </Button>
    </motion.form>
  );
}

export default PredictionForm;
