import type { FieldErrors } from "./errors";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export class ApiError extends Error {
  status: number;
  detail: string;
  errors: FieldErrors;

  constructor(status: number, detail: string, errors: FieldErrors = {}) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.errors = errors;
  }
}

function flattenErrors(raw: unknown): FieldErrors {
  if (!raw || typeof raw !== "object") return {};
  const errors: FieldErrors = {};
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    if (Array.isArray(value)) errors[key] = value.map(String);
    else if (typeof value === "string") errors[key] = [value];
  }
  return errors;
}

export function setSession(access: string, refresh: string) {
  localStorage.setItem("orbit.access", access);
  localStorage.setItem("orbit.refresh", refresh);
}

export function clearSession() {
  localStorage.removeItem("orbit.access");
  localStorage.removeItem("orbit.refresh");
}

export function hasSession() {
  return Boolean(localStorage.getItem("orbit.access") || localStorage.getItem("orbit.refresh"));
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refresh = localStorage.getItem("orbit.refresh");
  if (!refresh) return false;
  const response = await fetch(`${API_BASE}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    clearSession();
    return false;
  }
  const data = (await response.json()) as { access: string; refresh?: string };
  localStorage.setItem("orbit.access", data.access);
  if (data.refresh) localStorage.setItem("orbit.refresh", data.refresh);
  return true;
}

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const access = localStorage.getItem("orbit.access");
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const isAuthAttempt = path.startsWith("/auth/login") || path.startsWith("/auth/register") || path.startsWith("/auth/refresh");

  if (response.status === 401 && retry && !isAuthAttempt) {
    refreshInFlight ??= refreshTokens().finally(() => {
      refreshInFlight = null;
    });
    const refreshed = await refreshInFlight;
    if (refreshed) return api<T>(path, options, false);
    window.dispatchEvent(new Event("orbit:unauthorized"));
    throw new ApiError(401, "Your session expired. Sign in again.");
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  const body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
  if (!response.ok) {
    const errors = flattenErrors(body.errors);
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : errors.non_field_errors?.[0] || "The request could not be completed.";
    throw new ApiError(response.status, detail, errors);
  }
  return body as T;
}
