import type { SystemStatus } from "@/lib/api";

export function StatusPanel({ status }: { status: SystemStatus | null }) {
  if (!status) {
    return (
      <div className="rounded-lg border border-accent/40 bg-accent/5 p-4 text-sm">
        No se pudo contactar al backend. Verificá que FastAPI esté corriendo (
        <code>make backend</code>) y que <code>BACKEND_URL</code> sea correcto.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-surface">
      <table className="w-full text-sm">
        <thead className="bg-border/30 text-left text-xs uppercase text-muted">
          <tr>
            <th className="px-4 py-2">Componente</th>
            <th className="px-4 py-2">Tipo</th>
            <th className="px-4 py-2">Estado</th>
            <th className="px-4 py-2">Detalle</th>
          </tr>
        </thead>
        <tbody>
          {status.components.map((c) => {
            const label = !c.enabled ? "Desactivado" : c.available ? "Disponible" : "No disponible";
            const color = !c.enabled
              ? "text-muted"
              : c.available
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-amber-600 dark:text-amber-400";
            return (
              <tr key={c.name} className="border-t border-border">
                <td className="px-4 py-2 font-medium">{c.name}</td>
                <td className="px-4 py-2 text-muted">{c.kind === "tool" ? "Local" : "Externo"}</td>
                <td className={`px-4 py-2 ${color}`}>{label}</td>
                <td className="px-4 py-2 text-muted">{c.detail}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
