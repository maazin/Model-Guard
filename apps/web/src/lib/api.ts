export const API_BASE = import.meta.env.VITE_API_BASE ?? "";
const USER_KEY = "modelguard.user";

export function currentUser(): string {
  try {
    return localStorage.getItem(USER_KEY) ?? "reviewer";
  } catch {
    return "reviewer";
  }
}
const listeners = new Set<() => void>();
export function setCurrentUser(u: string) {
  try {
    localStorage.setItem(USER_KEY, u);
  } catch {
    /* ignore */
  }
  listeners.forEach((l) => l());
}
export function subscribeUser(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}

export class ApiError extends Error {
  status: number;
  problem: any;
  constructor(status: number, problem: any) {
    super(problem?.detail ?? `HTTP ${status}`);
    this.status = status;
    this.problem = problem;
  }
}

export async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Demo-User": currentUser(), ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    let problem: any = null;
    try {
      problem = await res.json();
    } catch {
      /* no body */
    }
    throw new ApiError(res.status, problem);
  }
  if (res.headers.get("content-type")?.includes("text/markdown")) return (await res.text()) as T;
  return (await res.json()) as T;
}

export const get = <T = any>(path: string) => api<T>(path);
export const post = <T = any>(path: string, body?: unknown) => api<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
export const put = <T = any>(path: string, body?: unknown) => api<T>(path, { method: "PUT", body: JSON.stringify(body) });
export const patch = <T = any>(path: string, body?: unknown) => api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
