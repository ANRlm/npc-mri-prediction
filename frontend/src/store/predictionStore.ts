import { create } from 'zustand';
import api from '@/api/client';
import type {
  PredictionData,
  PredictionRequest,
  SurvivalCurveData,
} from '@/types';

interface PredictionState {
  currentPrediction: PredictionData | null;
  survivalData: SurvivalCurveData | null;
  isLoading: boolean;
  error: string | null;
  predict: (req: PredictionRequest) => Promise<boolean>;
  uploadAndPredict: (formData: FormData) => Promise<boolean>;
  fetchSurvivalData: (req: PredictionRequest) => Promise<void>;
  reset: () => void;
}

export const usePredictionStore = create<PredictionState>((set) => ({
  currentPrediction: null,
  survivalData: null,
  isLoading: false,
  error: null,

  predict: async (req) => {
    set({ isLoading: true, error: null, currentPrediction: null, survivalData: null });
    try {
      const res = await api.post('/predict', req);
      if (res.data.success && res.data.data) {
        set({ currentPrediction: res.data.data, isLoading: false });
        return true;
      }
      set({ error: res.data.message || '预测失败', isLoading: false });
      return false;
    } catch (e: any) {
      const msg = e?.response?.data?.message || '预测失败，请检查输入参数';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  uploadAndPredict: async (formData) => {
    set({ isLoading: true, error: null, currentPrediction: null, survivalData: null });
    try {
      const res = await api.post('/upload-predict', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.success && res.data.data) {
        set({ currentPrediction: res.data.data, isLoading: false });
        return true;
      }
      set({ error: res.data.message || '预测失败', isLoading: false });
      return false;
    } catch (e: any) {
      const msg = e?.response?.data?.message || '预测失败，请检查上传文件';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  fetchSurvivalData: async (req) => {
    try {
      const res = await api.post('/survival-curve-data', req);
      if (res.data.success && res.data.data) {
        set({ survivalData: res.data.data });
      }
    } catch {
      // silent — chart shows empty state
    }
  },

  reset: () => set({ currentPrediction: null, survivalData: null, error: null }),
}));
