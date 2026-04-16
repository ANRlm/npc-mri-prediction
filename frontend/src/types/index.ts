export interface User {
  username: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  success: boolean;
  message?: string;
  token?: string;
  username?: string;
  email?: string;
}

export interface PredictionRequest {
  Patient_ID: string;
  性别: string;
  年龄: number;
  T分期: number;
  N分期: number;
  总分期: number;
  治疗前DNA: number;
  治疗后DNA: number;
}

export interface SurvivalRates {
  '1年生存率': string;
  '3年生存率': string;
  '5年生存率': string;
}

export interface Metrics {
  c_index: number;
  auc: number;
  sensitivity: number;
  specificity: number;
}

export interface PredictionData {
  id?: string;
  patient_id: string;
  risk_score: number;
  risk_group: '高风险组' | '低风险组';
  survival_rates: SurvivalRates;
  metrics: Metrics;
  clinical_advice: string[];
  survival_curve_base64?: string;
  timestamp: string;
}

export interface PredictionResponse {
  success: boolean;
  message?: string;
  data?: PredictionData;
}

export interface SurvivalCurveData {
  patient_id: string;
  risk_score: number;
  months: number[];
  survival_curves: {
    patient: number[];
    low_risk: number[];
    high_risk: number[];
  };
  reference_scores: number[];
  bar_chart: {
    labels: string[];
    patient_values: number[];
    low_risk_values: number[];
    high_risk_values: number[];
  };
}

export interface SurvivalCurveResponse {
  success: boolean;
  message?: string;
  data?: SurvivalCurveData;
}

export interface HistoryResponse {
  success: boolean;
  data: PredictionData[];
  count: number;
}

export interface FilesResponse {
  files: string[];
}

export type Theme = 'light' | 'dark' | 'auto';
