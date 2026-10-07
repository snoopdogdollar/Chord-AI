export type ApiEnvelope<T> =
  | { success: true; data: T; message?: string }
  | { success: false; error: { code: string; message: string } };

export type SubmitResponse = {
  song_id: string;
  job_id: string;
  status: string;
};

export type AnalysisRange = {
  start: number;
  end: number;
};

export type JobStatus = {
  job_id: string;
  song_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  stage: string | null;
  error_code?: string | null;
  error_message?: string | null;
};

export type SheetResponse = {
  song_id: string;
  title: string;
  pages: string[];
  notice: string;
  sections: Array<{ name: string; content: string[] }>;
};

export type ExportResponse = {
  export_id: string;
  download_url: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function unwrap<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiEnvelope<T>;
  if (!body.success) {
    throw new Error(body.error.message);
  }
  return body.data;
}

export async function uploadAudio(
  file: File,
  range?: AnalysisRange
): Promise<SubmitResponse> {
  const body = new FormData();
  body.append("file", file);

  if (range) {
    body.append("analysis_start_seconds", String(range.start));
    body.append("analysis_end_seconds", String(range.end));
  }

  const response = await fetch(`${API_BASE}/songs/upload`, { method: "POST", body });
  return unwrap<SubmitResponse>(response);
}

export async function submitYouTube(url: string): Promise<SubmitResponse> {
  const response = await fetch(`${API_BASE}/songs/youtube`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  return unwrap<SubmitResponse>(response);
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, { cache: "no-store" });
  return unwrap<JobStatus>(response);
}

export async function getSheet(songId: string): Promise<SheetResponse> {
  const response = await fetch(`${API_BASE}/songs/${songId}/sheet`, { cache: "no-store" });
  return unwrap<SheetResponse>(response);
}

export async function createExport(songId: string, format: "txt" | "pdf"): Promise<ExportResponse> {
  const response = await fetch(`${API_BASE}/songs/${songId}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format })
  });
  return unwrap<ExportResponse>(response);
}

export function absoluteDownloadUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }
  const base = API_BASE.replace(/\/api\/v1$/, "");
  return `${base}${path}`;
}
