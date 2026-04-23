import { request } from "./http";
import type {
  Caregiver,
  ChatPayload,
  DashboardSummary,
  MonthlyTrendItem,
  SensorRecord,
  StressDistributionItem,
} from "../types";

type Query = Record<string, string | undefined>;

function toQueryString(query: Query) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) {
      params.set(key, value);
    }
  }
  return params.toString();
}

export function getSensorRecords(month?: string, caregiverId?: string) {
  const qs = toQueryString({ month, caregiver_id: caregiverId });
  return request<SensorRecord[]>(`/api/sensor/records${qs ? `?${qs}` : ""}`);
}

export function getDashboardSummary(month?: string, caregiverId?: string) {
  const qs = toQueryString({ month, caregiver_id: caregiverId });
  return request<DashboardSummary>(`/api/dashboard/summary${qs ? `?${qs}` : ""}`);
}

export function getStressDistribution(month?: string, caregiverId?: string) {
  const qs = toQueryString({ month, caregiver_id: caregiverId });
  return request<StressDistributionItem[]>(
    `/api/dashboard/stress-distribution${qs ? `?${qs}` : ""}`,
  );
}

export function getMonthlyTrend(caregiverId?: string) {
  const qs = toQueryString({ caregiver_id: caregiverId });
  return request<MonthlyTrendItem[]>(`/api/dashboard/monthly-trend${qs ? `?${qs}` : ""}`);
}

export function getCaregivers() {
  return request<Caregiver[]>("/api/caregivers");
}

export function getCaregiverDetail(caregiverId: string) {
  return request<Caregiver>(`/api/caregivers/${encodeURIComponent(caregiverId)}`);
}

export async function sendChat(payload: ChatPayload) {
  const data = await request<{ reply?: string; message?: string }>("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const reply = (data.reply ?? data.message ?? "").trim();
  if (!reply) {
    throw new Error("Assistant returned an empty reply. Please try again.");
  }
  return reply;
}
