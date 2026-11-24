import { AddByUrl } from "@/components/radar/AddByUrl";
import { RadarClient } from "@/components/radar/RadarClient";

export default function RadarPage() {
  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Radar viral</h1>
        <p className="mt-1 text-sm text-muted">
          Busca videos públicos en YouTube y registra sus métricas en cada consulta. El crecimiento
          se calcula sólo cuando un video tiene al menos dos mediciones en momentos distintos.
        </p>
      </div>
      <AddByUrl />
      <RadarClient />
    </div>
  );
}
