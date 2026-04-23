import type { ApiResponse } from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

function toAbsoluteUrl(url: string) {
  if (/^https?:\/\//i.test(url)) return url;
  const normalized = url.startsWith("/") ? url : `/${url}`;
  if (!API_BASE_URL) return normalized;
  return `${API_BASE_URL}${normalized}`;
}

export async function request<T>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(toAbsoluteUrl(url), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  let payload: ApiResponse<T> | null = null;
  try {
    payload = (await response.json()) as ApiResponse<T>;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const nestedError =
      payload?.data && typeof payload.data === "object" && "error" in payload.data
        ? String((payload.data as Record<string, unknown>).error ?? "")
        : "";
    const message = payload?.error ?? (nestedError || `Request failed with status ${response.status}`);
    throw new Error(message);
  }

  if (!payload?.success) {
    throw new Error(payload?.error ?? "Request failed");
  }

  return payload.data as T;
}
