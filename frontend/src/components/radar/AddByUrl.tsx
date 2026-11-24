"use client";

import { useState } from "react";
import { clientJson } from "@/lib/api";
import type { Reference } from "@/lib/types";

export function AddByUrl() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const ref = await clientJson<Reference>("/api/references", {
        method: "POST", body: JSON.stringify({ url }),
      });
      const enriched = ref.view_count != null;
      setMsg({
        ok: true,
        text: enriched
          ? `Guardada: “${ref.title}”.`
          : `Guardada (#${ref.id}). Metadatos pendientes: se completan cuando YouTube esté configurado.`,
      });
      setUrl("");
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-2 text-sm font-medium">Agregar referencia por URL</div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="https://www.youtube.com/shorts/… o cualquier URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
        />
        <button type="submit" disabled={busy}
          className="rounded-md border border-border px-4 py-2 text-sm hover:border-accent disabled:opacity-50">
          {busy ? "Guardando…" : "Agregar"}
        </button>
      </div>
      {msg && (
        <p className={`mt-2 text-xs ${msg.ok ? "text-emerald-600 dark:text-emerald-400" : "text-accent"}`}>
          {msg.text}
        </p>
      )}
    </form>
  );
}
