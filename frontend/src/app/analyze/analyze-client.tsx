"use client";

import { type CSSProperties, type FormEvent, useMemo, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type JobInputType = "text" | "url" | "file";
type Phase = "idle" | "uploading" | "analyzing" | "done" | "error";

type MatchEvidence = {
  id: string;
  job_requirement_text: string;
  resume_evidence_text: string | null;
  match_type: string;
  match_status: string;
  confidence: number | null;
  explanation: string | null;
};

type MatchReport = {
  id: string;
  overall_score: number;
  analysis_confidence: number | null;
  breakdown_json: Record<string, unknown>;
  strengths_json: string[] | null;
  gaps_json: string[] | null;
  recommendations_json: string[] | null;
  ats_report_json: Record<string, unknown> | null;
  evidence: MatchEvidence[];
};

type RewriteSuggestion = {
  id: string;
  section_type: string;
  original_text: string | null;
  suggested_text: string;
  reason: string | null;
  estimated_score_lift: number | null;
  truth_status: string;
  guardrail_reason: string | null;
};

type Optimization = {
  id: string;
  score_before: number | null;
  score_after: number | null;
  status: string;
  suggestions: RewriteSuggestion[];
};

type AnalyzeResponse = {
  resume: {
    id: string;
    title: string;
    source_type: string;
    raw_text: string;
    parse_confidence: number | null;
  };
  job: {
    id: string;
    title: string | null;
    company: string | null;
    source_url: string | null;
    parse_confidence: number | null;
  };
  match_report: MatchReport;
  optimization: Optimization;
};

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
  const [resumeText, setResumeText] = useState(
    "Senior backend engineer with Python, FastAPI, PostgreSQL, Docker, and ML inference API experience. Built internal tooling for model-serving workflows and collaborated with data teams on deployment reliability.",
  );
  const [resumeTitle, setResumeTitle] = useState("Senior Backend Resume");
  const [jobInputType, setJobInputType] = useState<JobInputType>("text");
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [jobText, setJobText] = useState(
    "We are hiring an ML Platform Engineer to build Python and FastAPI services, improve PostgreSQL-backed platform tooling, strengthen observability, and partner across data and product teams.",
  );
  const [jobUrl, setJobUrl] = useState("");
  const [jobTitle, setJobTitle] = useState("ML Platform Engineer");
  const [company, setCompany] = useState("Acme AI");
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

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
          <p className="eyebrow">Live AI workbench</p>
          <h1 id="analyze-title">Add a resume and JD. Let the pipeline build the report.</h1>
          <p className="supporting-copy">
            Use files, pasted text, or a public job link. The backend extracts content, parses both
            documents, scores the match, and returns truth-guarded rewrite suggestions.
          </p>
        </div>
        <div className="hero-badges" aria-label="Supported analyze inputs">
          <span className="utility-chip">PDF</span>
          <span className="utility-chip">DOCX</span>
          <span className="utility-chip">TXT</span>
          <span className="utility-chip">URL</span>
        </div>
      </section>

      <section className="analysis-grid upload-analysis-grid" aria-label="Resume and JD analysis workspace">
        <form className="analysis-panel upload-form" onSubmit={handleSubmit}>
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Inputs</p>
              <h2>Source material</h2>
            </div>
            <p>Keep the demo copy for a fast smoke test, or replace it with real files.</p>
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
            <button
              className="primary-button analyze-submit-button"
              id="analyze-with-ai-button"
              type="submit"
              disabled={!canSubmit}
            >
              {isBusy ? "AI is analyzing..." : "Analyze with AI"}
            </button>
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

          {result ? <GeneratedReport result={result} /> : <EmptyReportPreview />}
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
        <span className="mini-tag">Waiting for input</span>
        <h2>Report preview will appear here</h2>
        <p className="supporting-copy">
          Submit the form to receive score breakdowns, evidence rows, strengths, gaps, and guarded
          resume rewrite suggestions from the backend.
        </p>
      </div>
    </div>
  );
}

function GeneratedReport({ result }: { result: AnalyzeResponse }) {
  const rows = buildBreakdownRows(result.match_report);
  const suggestions = result.optimization.suggestions.slice(0, 5);
  const evidenceRows = result.match_report.evidence.slice(0, 4);
  const projectedBefore = result.optimization.score_before ?? result.match_report.overall_score;
  const projectedAfter = result.optimization.score_after ?? result.match_report.overall_score;

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

async function errorFromResponse(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) return payload.detail.map((item) => JSON.stringify(item)).join("; ");
  } catch {
    // Fall through to text response.
  }
  return (await response.text()) || `Request failed with status ${response.status}`;
}
