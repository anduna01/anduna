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

/** Llamada desde el servidor de Next directo al backend (sin pasar por el navegador). */
export async function fetchSystemStatus(): Promise<SystemStatus | null> {
  const base = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${base}/api/system/status`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as SystemStatus;
  } catch {
    return null;
  }
}
