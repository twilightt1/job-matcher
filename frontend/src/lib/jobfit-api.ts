import type { JobRead, MatchReport, Optimization, ResumeRead } from "./jobfit-types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = RequestInit & {
  cache?: RequestCache;
};

export async function readMatchReport(reportId: string, options?: RequestOptions): Promise<MatchReport> {
  return readJson<MatchReport>(`/api/match-reports/${encodeURIComponent(reportId)}`, options);
}

export async function readResume(resumeId: string, options?: RequestOptions): Promise<ResumeRead> {
  return readJson<ResumeRead>(`/api/resumes/${encodeURIComponent(resumeId)}`, options);
}

export async function readJob(jobId: string, options?: RequestOptions): Promise<JobRead> {
  return readJson<JobRead>(`/api/jobs/${encodeURIComponent(jobId)}`, options);
}

export async function ensureOptimization(matchReportId: string): Promise<Optimization> {
  return readJson<Optimization>("/api/optimizations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ match_report_id: matchReportId }),
  });
}

export async function errorFromResponse(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) return payload.detail.map((item) => JSON.stringify(item)).join("; ");
  } catch {
    // Fall through to text response.
  }
  return (await response.text()) || `Request failed with status ${response.status}`;
}

async function readJson<T>(path: string, options?: RequestOptions): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...options,
  });

  if (!response.ok) {
    throw new Error(await errorFromResponse(response));
  }

  return (await response.json()) as T;
}
