export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: string;
};

export type SensorRecord = {
  id: string | number;
  date: string;
  time: string;
  datetime: string;
  X: number;
  Y: number;
  Z: number;
  EDA: number;
  HR: number;
  TEMP: number;
  MovementMagnitude: number;
  label: number;
};

export type DashboardSummary = {
  total_records: number;
  average_stress: number | null;
};

export type StressDistributionItem = {
  stress_value: number;
  count: number;
};

export type MonthlyTrendItem = {
  month: string;
  total_readings: number;
  average_stress: number | null;
};

export type Caregiver = Record<string, string | number | null>;

export type ChatPayload = {
  message: string;
  ui_state?: {
    selected_caregiver_id?: string;
    month_label?: string;
    active_view?: string;
    visualization_catalog?: Array<{
      id: string;
      label: string;
      path: string;
      tab?: string;
    }>;
  };
  heatmap_cell?: Record<string, unknown> | null;
};
