import { StatusPanel } from "@/components/StatusPanel";
import { fetchDashboard, fetchSystemStatus } from "@/lib/api";

export const dynamic = "force-dynamic";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}

function Meter({
  label,
  used,
  limit,
  fmt = String,
}: {
  label: string;
  used: number;
  limit: number;
  fmt?: (n: number) => string;
}) {
  const pct = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex justify-between gap-2 text-xs text-muted">
        <span>{label}</span>
        <span className="tabular-nums">
          {fmt(used)} / {fmt(limit)}
        </span>
      </div>
      <div className="mt-2 h-1.5 rounded-full bg-border">
        <div
          className={`h-1.5 rounded-full ${pct >= 90 ? "bg-accent" : "bg-emerald-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

const usd = (n: number) => `$${n.toFixed(2)}`;

export default async function DashboardPage() {
  const [status, data] = await Promise.all([fetchSystemStatus(), fetchDashboard()]);
  return (
    <div className="max-w-5xl space-y-8">
      <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
      {data && (
        <>
          <section className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Stat label="Referencias encontradas" value={data.references} />
            <Stat label="Videos analizados" value={data.analyzed} />
            <Stat label="Guiones generados" value={data.scripts} />
            <Stat label="Clips producidos" value={data.clips_produced} />
            <Stat label="Pendientes de revisión" value={data.clips_pending_review} />
            <Stat label="Clips aprobados" value={data.clips_approved} />
          </section>
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
              Uso y costos
            </h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Meter
                label="Costo estimado del mes (USD)"
                used={data.usage.month_cost_usd}
                limit={data.usage.monthly_budget_usd}
                fmt={usd}
              />
              <Meter
                label="Llamadas a Claude hoy"
                used={data.usage.claude_calls_today}
                limit={data.usage.claude_calls_limit}
              />
              <Meter
                label="Cuota YouTube hoy (unidades)"
                used={data.usage.youtube_units_today}
                limit={data.usage.youtube_units_limit}
              />
              <Meter
                label="Renders hoy"
                used={data.usage.renders_today}
                limit={data.usage.renders_limit}
              />
            </div>
          </section>
        </>
      )}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Estado del sistema
        </h2>
        <StatusPanel status={status} />
      </section>
    </div>
  );
}
