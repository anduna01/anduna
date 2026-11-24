export type ComponentStatus = {
  name: string;
  kind: "tool" | "provider";
  available: boolean;
  enabled: boolean;
  detail: string;
};

export type SystemStatus = {
  app: string;
  env: string;
  components: ComponentStatus[];
  limits: Record<string, number>;
};

export type UsageSummary = {
  claude_calls_today: number;
  claude_calls_limit: number;
  youtube_units_today: number;
  youtube_units_limit: number;
  renders_today: number;
  renders_limit: number;
  month_cost_usd: number;
  monthly_budget_usd: number;
};

export type DashboardData = {
  references: number;
  analyzed: number;
  scripts: number;
  clips_produced: number;
  clips_pending_review: number;
  clips_approved: number;
  usage: UsageSummary;
};

export type Job = {
  id: number;
  type: string;
  status: "queued" | "running" | "succeeded" | "failed";
  progress: number;
  result: Record<string, unknown> | null;
  error: string | null;
};

const BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

/** Desde componentes de servidor: directo al backend (no pasa por el navegador). */
export async function serverJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BACKEND}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const fetchSystemStatus = () => serverJson<SystemStatus>("/api/system/status");
export const fetchDashboard = () => serverJson<DashboardData>("/api/dashboard");

/** Desde el navegador: siempre rutas relativas /api (proxy de Next). */
export async function clientJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    const msg = typeof detail === "string" ? detail : (detail?.message ?? `Error ${res.status}`);
    throw new Error(msg);
  }
  return body as T;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Consulta un job hasta que termina. */
export async function waitForJob(id: number, onUpdate?: (j: Job) => void): Promise<Job> {
  let job = await clientJson<Job>(`/api/jobs/${id}`);
  onUpdate?.(job);
  while (job.status === "queued" || job.status === "running") {
    await sleep(1000);
    job = await clientJson<Job>(`/api/jobs/${id}`);
    onUpdate?.(job);
  }
  return job;
}
