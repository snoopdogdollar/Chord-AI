"use client";

import { create } from "zustand";
import {
  absoluteDownloadUrl,
  AnalysisRange,
  createExport,
  getJob,
  getSheet,
  JobStatus,
  SheetResponse,
  submitYouTube,
  uploadAudio
} from "@/services/api";

type WorkflowState = {
  job: JobStatus | null;
  sheet: SheetResponse | null;
  error: string | null;
  busy: boolean;
  submitFile: (file: File, range?: AnalysisRange) => Promise<void>;
  submitUrl: (url: string) => Promise<void>;
  refreshJob: () => Promise<void>;
  exportSheet: (format: "txt" | "pdf") => Promise<void>;
};

export const useChordAiWorkflow = create<WorkflowState>((set, get) => ({
  job: null,
  sheet: null,
  error: null,
  busy: false,
  async submitFile(file, range) {
    set({ busy: true, error: null, sheet: null });
    try {
      const submitted = await uploadAudio(file, range);
      set({
        job: {
          job_id: submitted.job_id,
          song_id: submitted.song_id,
          status: "queued",
          progress: 0,
          stage: null
        },
        busy: false
      });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Upload failed", busy: false });
    }
  },
  async submitUrl(url) {
    set({ busy: true, error: null, sheet: null });
    try {
      const submitted = await submitYouTube(url);
      set({
        job: {
          job_id: submitted.job_id,
          song_id: submitted.song_id,
          status: "queued",
          progress: 0,
          stage: null
        },
        busy: false
      });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "YouTube submission failed", busy: false });
    }
  },
  async refreshJob() {
    const current = get().job;
    if (!current || current.status === "completed" || current.status === "failed") {
      return;
    }
    try {
      const job = await getJob(current.job_id);
      set({ job });
      if (job.status === "completed") {
        const sheet = await getSheet(job.song_id);
        set({ sheet });
      }
      if (job.status === "failed") {
        set({ error: job.error_message ?? "Processing failed" });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Could not refresh job" });
    }
  },
  async exportSheet(format) {
    const current = get().job;
    if (!current || current.status !== "completed") {
      return;
    }
    try {
      const created = await createExport(current.song_id, format);
      window.location.href = absoluteDownloadUrl(created.download_url);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Export failed" });
    }
  }
}));
