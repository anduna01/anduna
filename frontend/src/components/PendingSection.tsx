import { NAV } from "@/lib/nav";

/** Marcador honesto para secciones aún no implementadas: no simula funcionalidad. */
export function PendingSection({ href, description }: { href: string; description: string }) {
  const item = NAV.find((n) => n.href === href)!;
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight">{item.label}</h1>
      <p className="mt-2 text-muted">{description}</p>
      <div className="mt-6 rounded-lg border border-dashed border-border bg-surface p-6 text-sm">
        Esta sección todavía no está implementada. Se habilita en la <b>Fase {item.phase}</b> del
        plan de desarrollo.
      </div>
    </div>
  );
}
