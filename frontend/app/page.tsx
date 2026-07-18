"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useChordAiWorkflow } from "@/features/useChordAiWorkflow";

export default function Home() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const { busy, error, exportSheet, job, refreshJob, sheet, submitFile, submitUrl } = useChordAiWorkflow();
  const sheetText = sheet?.sections.flatMap((section) => section.content).join("\n") ?? "";

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refreshJob();
    }, 1500);
    return () => window.clearInterval(timer);
  }, [refreshJob]);

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      void submitFile(file);
    }
  }

  function onYouTubeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (youtubeUrl.trim()) {
      void submitUrl(youtubeUrl.trim());
    }
  }

  const statusText = job ? `${job.status}${job.stage ? ` / ${job.stage}` : ""}` : "waiting";

  return (
    <main className="min-h-screen bg-paper">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-6">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-staff pb-4">
          <div>
            <h1 className="text-3xl font-semibold text-ink">ChordAI</h1>
            <p className="mt-1 text-sm text-slate-600">Audio to rehearsal chord sheet</p>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
            <span className="capitalize">{statusText.replaceAll("_", " ")}</span>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-[340px_1fr]">
          <div className="space-y-4">
            <div className="rounded border border-staff bg-white p-4">
              <label className="block text-sm font-semibold text-ink" htmlFor="audio-file">
                Audio file
              </label>
              <input
                id="audio-file"
                className="mt-3 block w-full rounded border border-staff bg-paper px-3 py-2 text-sm"
                type="file"
                accept=".mp3,.wav,.flac,.m4a,audio/*"
                disabled={busy}
                onChange={onFileChange}
              />
            </div>

            <form className="rounded border border-staff bg-white p-4" onSubmit={onYouTubeSubmit}>
              <label className="block text-sm font-semibold text-ink" htmlFor="youtube-url">
                YouTube URL
              </label>
              <input
                id="youtube-url"
                className="mt-3 block w-full rounded border border-staff bg-paper px-3 py-2 text-sm"
                type="url"
                value={youtubeUrl}
                disabled={busy}
                onChange={(event) => setYoutubeUrl(event.target.value)}
              />
              <button
                className="mt-3 w-full rounded bg-accent px-4 py-2 text-sm font-semibold text-white"
                type="submit"
                disabled={busy || !youtubeUrl.trim()}
              >
                Analyze
              </button>
            </form>

            <div className="rounded border border-staff bg-white p-4">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="font-semibold">Progress</span>
                <span>{job?.progress ?? 0}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded bg-paper">
                <div className="h-full bg-accent" style={{ width: `${job?.progress ?? 0}%` }} />
              </div>
              {error ? <p className="mt-3 text-sm text-warning">{error}</p> : null}
            </div>
          </div>

          <div className="rounded border border-staff bg-white p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-ink">Chord Sheet</h2>
              <div className="flex gap-2">
                <button
                  className="rounded border border-staff px-3 py-2 text-sm font-semibold"
                  disabled={job?.status !== "completed"}
                  onClick={() => void exportSheet("txt")}
                >
                  TXT
                </button>
                <button
                  className="rounded border border-staff px-3 py-2 text-sm font-semibold"
                  disabled={job?.status !== "completed"}
                  onClick={() => void exportSheet("pdf")}
                >
                  PDF
                </button>
              </div>
            </div>
            <pre className="min-h-[440px] overflow-auto rounded bg-paper p-4 font-mono text-sm leading-6 text-ink">{sheetText}</pre>
          </div>
        </section>
      </div>
    </main>
  );
}
