import { StatusPanel } from "@/components/StatusPanel";
import { fetchSystemStatus } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const status = await fetchSystemStatus();
  return (
    <div className="max-w-5xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-muted">
          Las métricas de referencias, análisis, guiones y clips se habilitan con la base de datos
          (Fase 2).
        </p>
      </div>
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Estado del sistema
        </h2>
        <StatusPanel status={status} />
      </section>
    </div>
  );
}
