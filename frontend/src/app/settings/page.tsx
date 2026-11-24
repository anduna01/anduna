import { SelfTestButton } from "@/components/SelfTestButton";
import { StatusPanel } from "@/components/StatusPanel";
import { fetchSystemStatus } from "@/lib/api";

export const dynamic = "force-dynamic";

const LIMIT_LABELS: Record<string, string> = {
  claude_calls_per_day: "Llamadas a Claude por día",
  youtube_units_per_day: "Unidades de cuota YouTube por día",
  monthly_budget_usd: "Presupuesto mensual (USD)",
  upload_mb: "Tamaño máximo de archivo (MB)",
  renders_per_day: "Renders por día",
};

export default async function SettingsPage() {
  const status = await fetchSystemStatus();
  return (
    <div className="max-w-5xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Configuración</h1>
        <p className="mt-1 text-muted">
          Las credenciales se definen en el archivo <code>.env</code> del servidor y nunca se
          muestran aquí. Para desactivar un proveedor usá <code>ANTHROPIC_ENABLED=false</code>,{" "}
          <code>YOUTUBE_ENABLED=false</code>, etc.
        </p>
      </div>
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">Proveedores</h2>
        <StatusPanel status={status} />
      </section>
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Diagnóstico
        </h2>
        <SelfTestButton />
      </section>
      {status && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            Límites de uso
          </h2>
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(status.limits).map(([k, v]) => (
              <div key={k} className="rounded-lg border border-border bg-surface p-4">
                <dt className="text-xs text-muted">{LIMIT_LABELS[k] ?? k}</dt>
                <dd className="mt-1 text-xl font-semibold">{v}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}
    </div>
  );
}
