"use client";

import { useState } from "react";
import { clientJson, waitForJob, type Job } from "@/lib/api";

export function SelfTestButton() {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const running = job !== null && (job.status === "queued" || job.status === "running");

  async function run() {
    setError(null);
    try {
      const j = await clientJson<Job>("/api/system/selftest", { method: "POST" });
      setJob(j);
      await waitForJob(j.id, setJob);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-4 text-sm">
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={run}
          disabled={running}
          className="rounded-md bg-accent px-3 py-1.5 font-medium text-white disabled:opacity-50"
        >
          {running ? "Renderizando…" : "Probar motor de render"}
        </button>
        <span className="text-muted">
          Genera 2 s de video 1080x1920 H.264/AAC con FFmpeg y lo verifica con ffprobe.
        </span>
      </div>
      {job?.status === "succeeded" && (
        <p className="mt-3 text-emerald-600 dark:text-emerald-400">
          OK: {String(job.result?.video)} · audio {String(job.result?.audio)}
        </p>
      )}
      {job?.status === "failed" && <p className="mt-3 text-accent">Falló: {job.error}</p>}
      {error && <p className="mt-3 text-accent">{error}</p>}
    </div>
  );
}
