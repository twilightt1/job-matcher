"use client";

import { type CSSProperties, type FormEvent, useMemo, useState } from "react";

import { API_BASE_URL, errorFromResponse } from "@/lib/jobfit-api";
import type { AnalyzeResponse, MatchReport } from "@/lib/jobfit-types";

type JobInputType = "text" | "url" | "file";
type Phase = "idle" | "uploading" | "analyzing" | "done" | "error";
type CopyState = "idle" | "copied" | "manual";

const DEMO_RESUME_TEXT = `
Senior Backend Engineer with 5 years of experience building Python, FastAPI, PostgreSQL, and Docker-based platforms for AI and data products.

Experience highlights:
- Designed FastAPI services for model inference workflows, reducing manual analyst handoffs by 40%.
- Built PostgreSQL-backed internal tooling with audit logs, background validation jobs, and CI checks.
- Partnered with data science teams to deploy ML prototypes into reliable production APIs.
- Improved observability with structured logs, health checks, and latency dashboards for critical services.

Core skills: Python, FastAPI, PostgreSQL, Docker, REST APIs, CI/CD, observability, data collaboration, ML platform tooling.
Languages: English, Vietnamese, Chinese, Japanese.
`.trim();
const DEMO_JOB_TEXT = `
We are hiring an ML Platform Engineer to build reliable product-facing AI infrastructure. The role requires strong Python and FastAPI experience, PostgreSQL-backed service design, Docker-based development workflows, API observability, and collaboration with data scientists and product teams across English, Vietnamese, Chinese, and Japanese-speaking markets.

Responsibilities:
- Build and maintain APIs that serve machine learning workflows.
- Improve reliability, logging, metrics, and deployment quality across AI services.
- Partner with data teams to turn prototypes into production-ready systems.
- Communicate trade-offs clearly and document technical decisions.

Preferred skills: Python, FastAPI, PostgreSQL, Docker, REST APIs, observability, CI/CD, ML platform experience, English, Vietnamese, Chinese, and Japanese communication.
`.trim();
const DEMO_RESUME_TITLE = "Senior Backend / ML Platform Resume";
const DEMO_JOB_TITLE = "ML Platform Engineer";
const DEMO_COMPANY = "Acme AI";

const inputModes: Array<{ id: JobInputType; label: string; copy: string }> = [
  { id: "text", label: "Paste JD", copy: "Best for protected boards" },
  { id: "url", label: "Job link", copy: "Public HTML pages" },
  { id: "file", label: "Upload JD", copy: "PDF, DOCX, TXT" },
];

const progressSteps = [
  { title: "Upload", copy: "Validate files, text, and links." },
  { title: "Extract", copy: "Convert PDF/DOCX/TXT or HTML into clean text." },
  { title: "Parse", copy: "Normalize resume and JD into schema-first JSON." },
  { title: "Match", copy: "Score skills, requirements, experience, and language." },
  { title: "Optimize", copy: "Truth-check every rewrite suggestion." },
];

export default function AnalyzePage() {
  const sessionId = useMemo(() => `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`, []);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState(DEMO_RESUME_TEXT);
  const [resumeTitle, setResumeTitle] = useState(DEMO_RESUME_TITLE);
  const [jobInputType, setJobInputType] = useState<JobInputType>("text");
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [jobText, setJobText] = useState(DEMO_JOB_TEXT);
  const [jobUrl, setJobUrl] = useState("");
  const [jobTitle, setJobTitle] = useState(DEMO_JOB_TITLE);
  const [company, setCompany] = useState(DEMO_COMPANY);
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [copyState, setCopyState] = useState<CopyState>("idle");

  const resumeReady = resumeFile !== null || resumeText.trim().length >= 20;
  const jobReady =
    (jobInputType === "text" && jobText.trim().length >= 50) ||
    (jobInputType === "url" && jobUrl.trim().length >= 10) ||
    (jobInputType === "file" && jobFile !== null);
  const isBusy = phase === "uploading" || phase === "analyzing";
  const canSubmit = resumeReady && jobReady && !isBusy;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      setErrorMessage("Please provide a resume and a valid job description source first.");
      setPhase("error");
      return;
    }

    setErrorMessage(null);
    setCopyState("idle");
    setPhase("uploading");

    const formData = new FormData();
    if (resumeFile) {
      formData.append("resume_file", resumeFile);
    } else {
      formData.append("resume_text", resumeText.trim());
    }
    formData.append("resume_title", resumeTitle.trim() || "Uploaded Resume");
    formData.append("job_input_type", jobInputType);
    formData.append("session_id", sessionId);

    if (jobTitle.trim()) {
      formData.append("job_title", jobTitle.trim());
    }
    if (company.trim()) {
      formData.append("company", company.trim());
    }

    if (jobInputType === "text") {
      formData.append("job_text", jobText.trim());
    } else if (jobInputType === "url") {
      formData.append("job_url", jobUrl.trim());
    } else if (jobFile) {
      formData.append("job_file", jobFile);
    }

    try {
      setPhase("analyzing");
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await errorFromResponse(response));
      }

      const payload = (await response.json()) as AnalyzeResponse;
      setResult(payload);
      setPhase("done");
    } catch (error) {
      setPhase("error");
      setErrorMessage(error instanceof Error ? error.message : "Failed to analyze the resume.");
    }
  }

  function handleLoadDemo() {
    setResumeFile(null);
    setResumeText(DEMO_RESUME_TEXT);
    setResumeTitle(DEMO_RESUME_TITLE);
    setJobInputType("text");
    setJobFile(null);
    setJobText(DEMO_JOB_TEXT);
    setJobUrl("");
    setJobTitle(DEMO_JOB_TITLE);
    setCompany(DEMO_COMPANY);
    setErrorMessage(null);
    setResult(null);
    setCopyState("idle");
    setPhase("idle");
  }

  function handleRunAnother() {
    setResult(null);
    setErrorMessage(null);
    setCopyState("idle");
    setPhase("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleCopyReportLink(reportId: string) {
    const url = buildReportUrl(reportId);
    try {
      await navigator.clipboard.writeText(url);
      setCopyState("copied");
    } catch {
      setCopyState("manual");
    }
  }

  return (
    <main className="page-shell analyze-shell">
      <nav className="topbar" aria-label="Analyze navigation">
        <a className="brand-group" href="/" id="analyze-home-brand">
          <span className="brand-badge" aria-hidden="true">
            JF
          </span>
          <span className="brand-meta">
            <span className="brand-title">JobFit AI</span>
            <span className="brand-caption">Analyze workbench</span>
          </span>
        </a>
        <div className="nav-links">
          <a className="nav-link" href="/" id="analyze-home-link">
            Overview
          </a>
          <a className="nav-link" href="/diagnostics" id="analyze-diagnostics-link">
            Diagnostics
          </a>
        </div>
      </nav>

      <section className="page-intro workbench-hero" aria-labelledby="analyze-title">
        <div>
          <p className="eyebrow">No-account product demo</p>
          <h1 id="analyze-title">Try the full CV/JD analysis flow in under a minute.</h1>
          <p className="supporting-copy">
            Start with the built-in sample or replace it with your own files. JobFit AI extracts the
            source material, scores the fit with evidence, then creates truth-guarded resume rewrites.
          </p>
        </div>
        <div className="hero-badges" aria-label="Supported analyze inputs">
          <span className="utility-chip">PDF</span>
          <span className="utility-chip">DOCX</span>
          <span className="utility-chip">TXT</span>
          <span className="utility-chip">URL</span>
          <span className="utility-chip">EN · VI · 中文 · 日本語</span>
        </div>
      </section>

      <section className="analysis-grid upload-analysis-grid" aria-label="Resume and JD analysis workspace">
        <form className="analysis-panel upload-form" onSubmit={handleSubmit}>
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Inputs</p>
              <h2>Source material</h2>
            </div>
            <p>Use the sample to validate the product instantly. No login, setup wizard, or account history required.</p>
          </div>

          <div className="form-stack">
            <div className="input-card upload-source-card">
              <div className="input-card-header">
                <div>
                  <label htmlFor="resume-upload-input">Resume / CV</label>
                  <span className="hint">Upload a document or use pasted fallback text.</span>
                </div>
                <span className={resumeReady ? "ready-dot ready" : "ready-dot"} aria-hidden="true" />
              </div>
              <label className="upload-zone" htmlFor="resume-upload-input">
                <input
                  id="resume-upload-input"
                  type="file"
                  accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
                />
                <span className="upload-icon" aria-hidden="true">
                  CV
                </span>
                <strong>{resumeFile ? resumeFile.name : "Choose resume file"}</strong>
                <small>{resumeFile ? formatFileSize(resumeFile.size) : "PDF, DOCX, or TXT"}</small>
              </label>
              <input
                className="text-input"
                id="resume-title-input"
                placeholder="Resume title"
                value={resumeTitle}
                onChange={(event) => setResumeTitle(event.target.value)}
              />
              {!resumeFile && (
                <textarea
                  id="resume-textarea"
                  value={resumeText}
                  onChange={(event) => setResumeText(event.target.value)}
                  placeholder="Paste resume text when you do not have a file..."
                />
              )}
            </div>

            <div className="input-card upload-source-card">
              <div className="input-card-header">
                <div>
                  <label htmlFor="job-textarea">Job description</label>
                  <span className="hint">Choose the fastest source for the target role.</span>
                </div>
                <span className={jobReady ? "ready-dot ready" : "ready-dot"} aria-hidden="true" />
              </div>

              <div className="segment-tabs" role="tablist" aria-label="Job description source type">
                {inputModes.map((mode) => (
                  <button
                    className={`segment-tab ${jobInputType === mode.id ? "active" : ""}`}
                    id={`job-mode-${mode.id}-button`}
                    key={mode.id}
                    type="button"
                    onClick={() => setJobInputType(mode.id)}
                  >
                    <strong>{mode.label}</strong>
                    <span>{mode.copy}</span>
                  </button>
                ))}
              </div>

              <div className="job-meta-grid">
                <input
                  className="text-input"
                  id="job-title-input"
                  placeholder="Job title"
                  value={jobTitle}
                  onChange={(event) => setJobTitle(event.target.value)}
                />
                <input
                  className="text-input"
                  id="company-input"
                  placeholder="Company"
                  value={company}
                  onChange={(event) => setCompany(event.target.value)}
                />
              </div>

              {jobInputType === "text" && (
                <textarea
                  id="job-textarea"
                  value={jobText}
                  onChange={(event) => setJobText(event.target.value)}
                  placeholder="Paste the job description..."
                />
              )}

              {jobInputType === "url" && (
                <input
                  className="text-input url-input"
                  id="job-url-input"
                  placeholder="https://company.com/careers/job-posting"
                  value={jobUrl}
                  onChange={(event) => setJobUrl(event.target.value)}
                />
              )}

              {jobInputType === "file" && (
                <label className="upload-zone compact-upload" htmlFor="job-upload-input">
                  <input
                    id="job-upload-input"
                    type="file"
                    accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                    onChange={(event) => setJobFile(event.target.files?.[0] ?? null)}
                  />
                  <span className="upload-icon" aria-hidden="true">
                    JD
                  </span>
                  <strong>{jobFile ? jobFile.name : "Choose JD file"}</strong>
                  <small>{jobFile ? formatFileSize(jobFile.size) : "PDF, DOCX, or TXT"}</small>
                </label>
              )}
            </div>
          </div>

          {errorMessage && (
            <div className="error-callout" role="alert">
              <strong>Analysis needs attention</strong>
              <p>{errorMessage}</p>
            </div>
          )}

          <div className="form-footer">
            <div>
              <strong>One-click AI pipeline</strong>
              <span>extract → parse → match → optimize → guard</span>
            </div>
            <div className="form-action-group">
              <button
                className="ghost-button demo-reset-button"
                id="load-demo-sample-button"
                type="button"
                onClick={handleLoadDemo}
              >
                Try demo data
              </button>
              <button
                className="primary-button analyze-submit-button"
                id="analyze-with-ai-button"
                type="submit"
                disabled={!canSubmit}
              >
                {isBusy ? "AI is analyzing..." : "Analyze with AI"}
              </button>
            </div>
          </div>
        </form>

        <article className="report-panel live-report-panel">
          <div className="panel-label">
            <span>Pipeline status</span>
            <span className={`score-pill status-pill ${phaseStatusClass(phase)}`}>
              {phaseLabel(phase)}
            </span>
          </div>

          <div className="phase-grid" aria-label="AI analysis progress">
            {progressSteps.map((step, index) => (
              <div className={`phase-card ${phaseIndex(phase) >= index ? "active" : ""}`} key={step.title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{step.title}</strong>
                <p>{step.copy}</p>
              </div>
            ))}
          </div>

          {result ? (
            <GeneratedReport
              copyState={copyState}
              result={result}
              onCopyReport={handleCopyReportLink}
              onRunAnother={handleRunAnother}
            />
          ) : (
            <EmptyReportPreview />
          )}
        </article>
      </section>
    </main>
  );
}

function EmptyReportPreview() {
  return (
    <div className="empty-report-preview">
      <div className="score-orb mini-score-orb">
        <span className="score-value">AI</span>
      </div>
      <div>
        <span className="mini-tag">No-account demo ready</span>
        <h2>Report preview will appear here</h2>
        <p className="supporting-copy">
          Use the pre-filled sample and click Analyze with AI to generate a shareable report. Replace
          the text or upload real files when you want to test your own target role.
        </p>
      </div>
    </div>
  );
}

function GeneratedReport({
  result,
  copyState,
  onCopyReport,
  onRunAnother,
}: {
  result: AnalyzeResponse;
  copyState: CopyState;
  onCopyReport: (reportId: string) => void;
  onRunAnother: () => void;
}) {
  const rows = buildBreakdownRows(result.match_report);
  const suggestions = result.optimization.suggestions.slice(0, 5);
  const evidenceRows = result.match_report.evidence.slice(0, 4);
  const projectedBefore = result.optimization.score_before ?? result.match_report.overall_score;
  const projectedAfter = result.optimization.score_after ?? result.match_report.overall_score;
  const reportPath = `/reports/${result.match_report.id}`;

  return (
    <div className="generated-report">
      <section className="result-hero-card" aria-labelledby="generated-report-title">
        <div
          className="score-orb live-score-orb"
          style={{ "--score": `${result.match_report.overall_score}%` } as CSSProperties}
        >
          <span className="score-value">{result.match_report.overall_score}%</span>
        </div>
        <div>
          <span className="mini-tag">Generated report</span>
          <h2 id="generated-report-title">
            {result.job.title ?? "Target role"} {result.job.company ? `· ${result.job.company}` : ""}
          </h2>
          <p>
            Resume source: <strong>{result.resume.source_type}</strong>. Confidence:{" "}
            {formatPercent(result.match_report.analysis_confidence)}. Projected score:{" "}
            {projectedBefore}% → {projectedAfter}%.
          </p>
        </div>
      </section>

      <div className="report-action-strip analyze-report-actions" aria-label="Generated report actions">
        <a className="primary-button" href={reportPath} id="view-full-report-link">
          View full report
        </a>
        <button
          className="secondary-button"
          id="copy-generated-report-link-button"
          type="button"
          onClick={() => onCopyReport(result.match_report.id)}
        >
          {copyState === "copied" ? "Link copied" : copyState === "manual" ? "Open report to copy" : "Copy link"}
        </button>
        <button className="ghost-button" id="run-another-analysis-button" type="button" onClick={onRunAnother}>
          Run another
        </button>
      </div>

      <div className="score-breakdown compact-breakdown">
        {rows.map((item) => (
          <div className="progress-row" key={item.label}>
            <div className="progress-meta">
              <span>{item.label}</span>
              <span>{item.value}%</span>
            </div>
            <div className="progress-bar" aria-hidden="true">
              <div className="progress-fill" style={{ width: `${item.value}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="report-grid">
        <InsightList title="Strengths" tag="strengths_json" items={result.match_report.strengths_json ?? []} />
        <InsightList title="Gaps" tag="gaps_json" items={result.match_report.gaps_json ?? []} danger />
      </div>

      <section className="evidence-stack" aria-labelledby="evidence-title">
        <div className="panel-label">
          <h2 id="evidence-title">Evidence rows</h2>
          <span className="code-chip">match_evidence</span>
        </div>
        {(evidenceRows.length ? evidenceRows : []).map((item) => (
          <article className="evidence-row-card" key={item.id}>
            <header>
              <span className={`status-pill ${item.match_status === "missing" ? "danger" : "success"}`}>
                {item.match_status}
              </span>
              <span className="code-chip">{item.match_type}</span>
            </header>
            <strong>{item.job_requirement_text}</strong>
            <p>{item.resume_evidence_text ?? item.explanation ?? "No direct resume evidence found."}</p>
          </article>
        ))}
        {!evidenceRows.length && <p className="empty-note">No evidence rows returned for this report.</p>}
      </section>

      <section className="optimizer-grid live-optimizer-grid" aria-label="Truth guarded rewrite suggestions">
        {(suggestions.length ? suggestions : []).map((suggestion) => (
          <article className="optimizer-card" key={suggestion.id}>
            <header>
              <span className={`status-pill ${truthStatusClass(suggestion.truth_status)}`}>
                {suggestion.truth_status}
              </span>
              <span className="code-chip">+{suggestion.estimated_score_lift ?? 0} pts</span>
            </header>
            <h3>{humanize(suggestion.section_type)}</h3>
            <p>{suggestion.suggested_text}</p>
            {suggestion.guardrail_reason && <small>{suggestion.guardrail_reason}</small>}
          </article>
        ))}
        {!suggestions.length && <p className="empty-note">No optimizer suggestions returned yet.</p>}
      </section>
    </div>
  );
}

function InsightList({
  title,
  tag,
  items,
  danger = false,
}: {
  title: string;
  tag: string;
  items: string[];
  danger?: boolean;
}) {
  return (
    <div className={danger ? "evidence-card" : "insight-card"}>
      <header>
        <span className="mini-tag">{title}</span>
        <span className="code-chip">{tag}</span>
      </header>
      <h3>{title === "Strengths" ? "Where the candidate aligns" : "What to improve"}</h3>
      <ul className={danger ? "gap-list" : "strength-list"}>
        {(items.length ? items : ["No items returned by the backend for this section."]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function buildBreakdownRows(report: MatchReport) {
  const breakdown = report.breakdown_json;
  return [
    { label: "Skills", value: scoreFromBreakdown(breakdown.skills) },
    { label: "Requirements", value: scoreFromBreakdown(breakdown.requirements) },
    { label: "Experience", value: scoreFromBreakdown(breakdown.experience) },
    { label: "Languages", value: scoreFromBreakdown(breakdown.languages) },
  ];
}

function scoreFromBreakdown(value: unknown): number {
  if (typeof value === "number") {
    return clamp(Math.round(value));
  }
  if (value && typeof value === "object" && "score" in value) {
    const score = (value as { score?: unknown }).score;
    if (typeof score === "number") {
      return clamp(Math.round(score));
    }
  }
  return 0;
}

function phaseIndex(phase: Phase): number {
  if (phase === "idle") return -1;
  if (phase === "uploading") return 1;
  if (phase === "analyzing") return 3;
  if (phase === "done") return 4;
  return 0;
}

function phaseLabel(phase: Phase): string {
  if (phase === "uploading") return "extracting";
  if (phase === "analyzing") return "ai running";
  if (phase === "done") return "complete";
  if (phase === "error") return "needs input";
  return "ready";
}

function phaseStatusClass(phase: Phase): string {
  if (phase === "done") return "success";
  if (phase === "error") return "danger";
  if (phase === "idle") return "neutral";
  return "warning";
}

function truthStatusClass(status: string): string {
  if (status === "safe") return "success";
  if (status === "needs_review") return "warning";
  return "danger";
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatPercent(value: number | null): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function buildReportUrl(reportId: string): string {
  if (typeof window === "undefined") {
    return `/reports/${reportId}`;
  }
  return `${window.location.origin}/reports/${reportId}`;
}
