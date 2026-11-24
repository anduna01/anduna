import { fmtCompact } from "@/lib/format";
import type { Growth } from "@/lib/types";

/** Crecimiento sólo con ≥2 mediciones; si no, lo dice explícitamente. */
export function GrowthBadge({ growth }: { growth: Growth | null }) {
  if (!growth || !growth.sufficient_data) {
    const n = growth?.snapshots ?? 0;
    return (
      <span
        className="rounded bg-border/60 px-1.5 py-0.5 text-[11px] text-muted"
        title="Se necesitan al menos 2 mediciones en momentos distintos para calcular crecimiento."
      >
        Sin historial ({n} {n === 1 ? "medición" : "mediciones"})
      </span>
    );
  }
  return (
    <span
      className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[11px] text-emerald-700 dark:text-emerald-400"
      title={`${growth.snapshots} mediciones en ${growth.hours_span} h · +${growth.view_delta} vistas`}
    >
      +{fmtCompact(growth.views_per_hour_recent)} vistas/h (medido)
    </span>
  );
}
