"use client";

import { useEffect, useState } from "react";
import { GrowthBadge } from "@/components/GrowthBadge";
import { clientJson } from "@/lib/api";
import { fmtAgo, fmtCompact, fmtDuration } from "@/lib/format";
import type { Category, RadarResult, RadarVideo, Reference } from "@/lib/types";

const LANGUAGES = [
  ["", "Cualquier idioma"], ["es", "Español"], ["en", "Inglés"], ["pt", "Portugués"],
  ["fr", "Francés"], ["it", "Italiano"], ["de", "Alemán"],
];
const REGIONS = [
  ["", "Cualquier país"], ["AR", "Argentina"], ["MX", "México"], ["ES", "España"],
  ["CO", "Colombia"], ["CL", "Chile"], ["PE", "Perú"], ["US", "Estados Unidos"],
  ["BR", "Brasil"], ["GB", "Reino Unido"],
];
const AGES = [
  ["", "Cualquier fecha"], ["1", "Últimas 24 h"], ["7", "Última semana"], ["30", "Último mes"],
  ["90", "Últimos 3 meses"], ["365", "Último año"],
];
const DURATIONS = [
  ["", "Cualquier duración"], ["short", "Corto (< 4 min)"], ["medium", "Medio (4–20 min)"],
  ["long", "Largo (> 20 min)"],
];
const ORDERS = [
  ["viewCount", "Más vistos"], ["date", "Más recientes"], ["relevance", "Relevancia"],
  ["rating", "Mejor valorados"],
];

type Form = {
  mode: "search" | "trending";
  q: string;
  category_id: string;
  language: string;
  region: string;
  max_age_days: string;
  duration: string;
  min_seconds: string;
  max_seconds: string;
  order: string;
};

const initial: Form = {
  mode: "search", q: "", category_id: "", language: "es", region: "", max_age_days: "30",
  duration: "", min_seconds: "", max_seconds: "", order: "viewCount",
};

const input =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent";

function Select({ value, onChange, options, label }: {
  value: string; onChange: (v: string) => void; options: string[][]; label: string;
}) {
  return (
    <label className="block text-xs text-muted">
      {label}
      <select className={`${input} mt-1 text-foreground`} value={value}
        onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}

function buildBody(f: Form, pageToken?: string | null) {
  const num = (s: string) => (s.trim() === "" ? null : Number(s));
  return {
    mode: f.mode,
    q: f.mode === "search" ? f.q.trim() || null : null,
    category_id: f.category_id || null,
    language: f.language || null,
    region: f.region || null,
    max_age_days: f.mode === "search" ? num(f.max_age_days) : null,
    duration: f.mode === "search" ? f.duration || null : null,
    min_seconds: num(f.min_seconds),
    max_seconds: num(f.max_seconds),
    order: f.order,
    max_results: 25,
    page_token: pageToken ?? null,
  };
}

export function RadarClient() {
  const [form, setForm] = useState<Form>(initial);
  const [categories, setCategories] = useState<Category[]>([]);
  const [catError, setCatError] = useState<string | null>(null);
  const [result, setResult] = useState<RadarResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<Set<string>>(new Set());
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm((f) => ({ ...f, [k]: v }));

  useEffect(() => {
    const params = new URLSearchParams({ region: form.region || "US" });
    if (form.language) params.set("hl", form.language);
    clientJson<Category[]>(`/api/radar/categories?${params}`)
      .then((c) => { setCategories(c); setCatError(null); })
      .catch((e: Error) => setCatError(e.message));
  }, [form.region, form.language]);

  async function run(pageToken?: string | null) {
    setLoading(true);
    setError(null);
    try {
      const res = await clientJson<RadarResult>("/api/radar/search", {
        method: "POST", body: JSON.stringify(buildBody(form, pageToken)),
      });
      setResult((prev) => pageToken && prev
        ? { ...res, videos: [...prev.videos, ...res.videos] } : res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function save(v: RadarVideo) {
    setSaving((s) => new Set(s).add(v.youtube_id));
    try {
      const refs = await clientJson<Reference[]>("/api/radar/save", {
        method: "POST", body: JSON.stringify({ youtube_ids: [v.youtube_id] }),
      });
      const id = refs[0]?.id ?? null;
      setResult((r) => r && {
        ...r,
        videos: r.videos.map((x) => x.youtube_id === v.youtube_id ? { ...x, reference_id: id ?? -1 } : x),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving((s) => { const n = new Set(s); n.delete(v.youtube_id); return n; });
    }
  }

  return (
    <div className="space-y-6">
      <form
        className="space-y-4 rounded-lg border border-border bg-surface p-4"
        onSubmit={(e) => { e.preventDefault(); run(); }}
      >
        <div className="flex gap-2 text-sm">
          {(["search", "trending"] as const).map((m) => (
            <button key={m} type="button" onClick={() => set("mode", m)}
              className={`rounded-md px-3 py-1.5 ${form.mode === m ? "bg-accent text-white" : "bg-border/50"}`}>
              {m === "search" ? "Búsqueda" : "Tendencias por categoría"}
            </button>
          ))}
        </div>
        {form.mode === "search" && (
          <input className={input} placeholder="Palabras clave (ej.: misterios sin resolver)"
            value={form.q} onChange={(e) => set("q", e.target.value)} />
        )}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-xs text-muted">
            Categoría
            <select className={`${input} mt-1 text-foreground`} value={form.category_id}
              onChange={(e) => set("category_id", e.target.value)} disabled={!!catError}>
              <option value="">Todas las categorías</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          </label>
          <Select label="Idioma" value={form.language} onChange={(v) => set("language", v)} options={LANGUAGES} />
          <Select label="País" value={form.region} onChange={(v) => set("region", v)} options={REGIONS} />
          <Select label="Orden" value={form.order} onChange={(v) => set("order", v)} options={ORDERS} />
          {form.mode === "search" && (
            <>
              <Select label="Antigüedad máxima" value={form.max_age_days}
                onChange={(v) => set("max_age_days", v)} options={AGES} />
              <Select label="Duración (YouTube)" value={form.duration}
                onChange={(v) => set("duration", v)} options={DURATIONS} />
            </>
          )}
          <label className="block text-xs text-muted">
            Duración mínima (s)
            <input className={`${input} mt-1`} type="number" min={0} value={form.min_seconds}
              onChange={(e) => set("min_seconds", e.target.value)} />
          </label>
          <label className="block text-xs text-muted">
            Duración máxima (s)
            <input className={`${input} mt-1`} type="number" min={1} value={form.max_seconds}
              onChange={(e) => set("max_seconds", e.target.value)} />
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button type="submit" disabled={loading}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {loading ? "Buscando…" : "Buscar"}
          </button>
          <span className="text-xs text-muted">
            Costo de cuota: {form.mode === "search" ? "~101 unidades por búsqueda" : "1 unidad"}.
          </span>
        </div>
        {catError && <p className="text-xs text-amber-600">Categorías no disponibles: {catError}</p>}
      </form>

      {error && (
        <div className="rounded-lg border border-accent/40 bg-accent/5 p-3 text-sm">{error}</div>
      )}

      {result && (
        <div className="space-y-3">
          <p className="text-xs text-muted">
            {result.videos.length} videos
            {result.total_results != null && ` · ~${fmtCompact(result.total_results)} resultados en YouTube`}
            {result.filtered_out > 0 && ` · ${result.filtered_out} excluidos por duración`}
            {" · "}Las vistas/día son un promedio desde la publicación, no una medición de crecimiento.
          </p>
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {result.videos.map((v) => (
              <li key={v.youtube_id} className="flex flex-col overflow-hidden rounded-lg border border-border bg-surface">
                <a href={v.url} target="_blank" rel="noreferrer" className="relative block aspect-video bg-border">
                  {v.thumbnail_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={v.thumbnail_url} alt="" className="h-full w-full object-cover" loading="lazy"
                      onError={(e) => { e.currentTarget.style.visibility = "hidden"; }} />
                  )}
                  <span className="absolute bottom-1 right-1 rounded bg-black/75 px-1.5 text-xs text-white">
                    {fmtDuration(v.duration_seconds)}
                  </span>
                </a>
                <div className="flex flex-1 flex-col gap-2 p-3">
                  <a href={v.url} target="_blank" rel="noreferrer"
                    className="line-clamp-2 text-sm font-medium hover:underline">{v.title}</a>
                  <div className="text-xs text-muted">
                    {v.channel_title} · {fmtAgo(v.published_at)}
                  </div>
                  <div className="flex flex-wrap gap-x-3 text-xs">
                    <span><b>{fmtCompact(v.view_count)}</b> vistas</span>
                    <span>{fmtCompact(v.avg_views_per_day)} /día prom.</span>
                    <span>{fmtCompact(v.like_count)} likes</span>
                  </div>
                  <div><GrowthBadge growth={v.growth} /></div>
                  <div className="mt-auto pt-1">
                    {v.reference_id ? (
                      <span className="text-xs text-emerald-600 dark:text-emerald-400">✓ En la biblioteca</span>
                    ) : (
                      <button onClick={() => save(v)} disabled={saving.has(v.youtube_id)}
                        className="rounded-md border border-border px-3 py-1 text-xs hover:border-accent disabled:opacity-50">
                        {saving.has(v.youtube_id) ? "Guardando…" : "Guardar referencia"}
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
          {result.next_page_token && (
            <button onClick={() => run(result.next_page_token)} disabled={loading}
              className="rounded-md border border-border px-4 py-2 text-sm disabled:opacity-50">
              {loading ? "Cargando…" : "Cargar más"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
