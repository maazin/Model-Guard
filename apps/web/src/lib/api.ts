export const API_BASE = import.meta.env.VITE_API_BASE ?? "";
/** Read-only public demo: GETs are served from a static export of the seeded API; mutations are refused. */
export const STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === "true";
export const REPO_URL = import.meta.env.VITE_REPO_URL ?? "https://github.com/maazin/Model-Guard";
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

const READ_ONLY_PROBLEM = {
  type: "urn:modelguard:read-only-demo",
  title: "Read-only public demo",
  status: 405,
  detail:
    "This hosted demo serves a snapshot of the seeded registry. Approvals, alert resolution, training and document edits run against the real API — clone the repository and run `make docker-up` to use the full workflow.",
};

async function staticGet<T>(path: string): Promise<T> {
  const clean = path.replace(/^\/api\/v1/, "").split("?")[0].replace(/^\//, "");
  const res = await fetch(`${import.meta.env.BASE_URL}demo-data/${clean}.json`);
  if (!res.ok) throw new ApiError(res.status, { title: "Not found", status: res.status, detail: `No demo data for ${path}` });
  return (await res.json()) as T;
}

export async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  if (STATIC_DEMO) {
    if (method === "GET") return staticGet<T>(path);
    if (method === "POST" && path.endsWith("/copilot/query")) return staticGet<T>(path);
    throw new ApiError(405, READ_ONLY_PROBLEM);
  }
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
