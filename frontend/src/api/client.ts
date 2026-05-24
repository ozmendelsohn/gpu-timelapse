export type OutputFormat = "mp4" | "gif" | "webm";
export type SpeedMode = "multiplier" | "duration";
export type JobStatus = "pending" | "processing" | "done" | "error";

export interface UploadResponse {
  job_id: string;
  filename: string;
  size: number;
}

export interface ProcessRequest {
  job_id: string;
  mode: SpeedMode;
  value: number;
  format: OutputFormat;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  error: string;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

export async function uploadVideo(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/upload", { method: "POST", body: form });
  return handleResponse<UploadResponse>(res);
}

export async function startProcessing(req: ProcessRequest): Promise<{ job_id: string; status: string }> {
  const res = await fetch("/api/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return handleResponse(res);
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`/api/jobs/${jobId}/status`);
  return handleResponse<JobStatusResponse>(res);
}

export function getDownloadUrl(jobId: string): string {
  return `/api/jobs/${jobId}/download`;
}
