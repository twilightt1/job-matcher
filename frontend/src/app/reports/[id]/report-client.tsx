"use client";

import { type CSSProperties, useEffect, useMemo, useState } from "react";

import { ensureOptimization, readJob, readMatchReport, readResume } from "@/lib/jobfit-api";
import type {
  JobRead,
  MatchEvidence,
  MatchReport,
  Optimization,
  ResumeRead,
  RewriteSuggestion,
} from "@/lib/jobfit-types";

type LoadState = "loading" | "ready" | "error";
type CopyState = "idle" | "copied" | "manual";

type ReportBundle = {
  report: MatchReport;
  resume: ResumeRead;
  job: JobRead;
  optimization: Optimization;
};

export default function ReportClient({ reportId }: { reportId: string }) {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [bundle, setBundle] = useState<ReportBundle | null>(null);
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadReport() {
      setLoadState("loading");
      setErrorMessage(null);
      setCopyState("idle");

      try {
        const report = await readMatchReport(reportId);
        const [resume, job, optimization] = await Promise.all([
          readResume(report.resume_id),
          readJob(report.job_id),
          ensureOptimization(report.id),
        ]);

        if (!cancelled) {
          setBundle({ report, resume, job, optimization });
          setLoadState("ready");
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(error instanceof Error ? error.message : "Failed to load report.");
          setLoadState("error");
        }
      }
    }

    loadReport();

    return () => {
      cancelled = true;
    };
  }, [reportId, reloadNonce]);

  const reportUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return `/reports/${reportId}`;
    }
    return window.location.href;
  }, [reportId]);

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(reportUrl);
      setCopyState("copied");
    } catch {
      setCopyState("manual");
    }
  }

  function handleDownloadMarkdown() {
    if (!bundle) return;

    const markdown = buildMarkdownReport(bundle, reportUrl);
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = `jobfit-report-${bundle.report.id.slice(0, 8)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
  }

  return (
    <main className="page-shell report-detail-shell">
      <nav className="topbar" aria-label="Report navigation">
        <a className="brand-group" href="/" id="report-home-brand">
          <span className="brand-badge" aria-hidden="true">
            JF
          </span>
          <span className="brand-meta">
            <span className="brand-title">JobFit AI</span>
            <span className="brand-caption">Shareable match report</span>
          </span>
        </a>
        <div className="nav-links">
          <a className="nav-link" href="/analyze" id="report-analyze-link">
            Analyze
          </a>
          <a className="nav-link" href="/diagnostics" id="report-diagnostics-link">
            Diagnostics
          </a>
        </div>
      </nav>

      {loadState === "loading" && <ReportLoadingState />}

      {loadState === "error" && (
        <section className="report-state-card" role="alert" aria-labelledby="report-error-title">
          <span className="status-pill danger">Load failed</span>
          <h1 id="report-error-title">Could not open this report.</h1>
          <p>{errorMessage ?? "The report may not exist yet, or the backend API is unavailable."}</p>
          <div className="report-action-strip">
            <button
              className="primary-button"
              id="retry-report-load-button"
              type="button"
              onClick={() => setReloadNonce((value) => value + 1)}
            >
              Retry
            </button>
            <a className="secondary-button" href="/analyze" id="error-back-to-analyze-link">
              Back to analyze
            </a>
          </div>
        </section>
      )}

      {loadState === "ready" && bundle && (
        <ReportContent
          bundle={bundle}
          copyState={copyState}
          reportUrl={reportUrl}
          onCopyLink={handleCopyLink}
          onDownloadMarkdown={handleDownloadMarkdown}
          onRefresh={() => setReloadNonce((value) => value + 1)}
        />
      )}
    </main>
  );
}

function ReportLoadingState() {
  return (
    <section className="report-state-card report-loading-card" aria-label="Report loading state">
      <span className="status-pill warning">Loading report</span>
      <h1>Building the shareable report view...</h1>
      <p>
        Fetching the match score, resume/job records, evidence rows, and the latest truth-guarded
        optimization draft from the backend.
      </p>
      <div className="report-loading-grid" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </section>
  );
}

function ReportContent({
  bundle,
  copyState,
  reportUrl,
  onCopyLink,
  onDownloadMarkdown,
  onRefresh,
}: {
  bundle: ReportBundle;
  copyState: CopyState;
  reportUrl: string;
  onCopyLink: () => void;
  onDownloadMarkdown: () => void;
  onRefresh: () => void;
}) {
  const { report, resume, job, optimization } = bundle;
  const rows = buildBreakdownRows(report);
  const matchedKeywords = readStringArray(report.ats_report_json, "keywords_matched");
  const missingKeywords = readStringArray(report.ats_report_json, "keywords_missing");
  const atsWarnings = readStringArray(report.ats_report_json, "warnings");
  const riskySuggestions = optimization.suggestions.filter((item) => item.truth_status !== "safe");
  const projectedBefore = optimization.score_before ?? report.overall_score;
  const projectedAfter = optimization.score_after ?? report.overall_score;
  const createdAt = report.created_at ? new Date(report.created_at).toLocaleString() : "Just now";

  return (
    <>
      <section className="report-detail-hero" aria-labelledby="report-detail-title">
        <div className="report-score-panel">
          <div
            className="score-orb report-score-orb"
            style={{ "--score": `${report.overall_score}%` } as CSSProperties}
          >
            <span className="score-value">{report.overall_score}%</span>
          </div>
          <span className={`score-pill ${scoreTone(report.overall_score)}`}>{scoreLabel(report.overall_score)}</span>
        </div>

        <div className="report-hero-copy">
          <p className="eyebrow">Explainable match report</p>
          <h1 id="report-detail-title">
            {job.title ?? "Target role"} {job.company ? `for ${job.company}` : ""}
          </h1>
          <p className="supporting-copy">
            Generated from <strong>{resume.title}</strong>. This report connects deterministic score
            breakdowns, requirement-level evidence, ATS keyword gaps, and guarded resume rewrites.
          </p>
          <div className="report-meta-grid" aria-label="Report summary metrics">
            <MetricTile label="Analysis confidence" value={formatPercent(report.analysis_confidence)} />
            <MetricTile label="Projected lift" value={`${projectedBefore}% → ${projectedAfter}%`} />
            <MetricTile label="Evidence rows" value={String(report.evidence.length)} />
            <MetricTile label="Created" value={createdAt} compact />
          </div>
        </div>
      </section>

      <div className="report-action-strip sticky-report-actions" aria-label="Report actions">
        <a className="primary-button" href="/analyze" id="report-new-analysis-link">
          New analysis
        </a>
        <button className="secondary-button" id="copy-report-link-button" type="button" onClick={onCopyLink}>
          {copyState === "copied" ? "Link copied" : "Copy share link"}
        </button>
        <button
          className="secondary-button"
          id="download-report-markdown-button"
          type="button"
          onClick={onDownloadMarkdown}
        >
          Export markdown
        </button>
        <button className="ghost-button" id="refresh-report-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
      </div>
      {copyState === "manual" && <p className="copy-fallback-note">Copy this URL manually: {reportUrl}</p>}

      {riskySuggestions.length > 0 && <TruthGuardWarning suggestions={riskySuggestions} />}

      <section className="report-detail-grid" aria-label="Report detail sections">
        <article className="report-section-card score-section-card">
          <header>
            <span className="mini-tag">Score model</span>
            <span className="code-chip">breakdown_json</span>
          </header>
          <h2>Why this score happened</h2>
          <div className="score-breakdown report-detail-breakdown">
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
        </article>

        <article className="report-section-card ats-section-card">
          <header>
            <span className="mini-tag">ATS coverage</span>
            <span className="code-chip">ats_report_json</span>
          </header>
          <h2>Keywords to keep visible</h2>
          <KeywordCloud title="Matched" keywords={matchedKeywords} tone="success" />
          <KeywordCloud title="Missing" keywords={missingKeywords} tone="danger" />
          {atsWarnings.length > 0 && <InlineWarnings warnings={atsWarnings} />}
        </article>

        <ReportListCard
          title="Strengths"
          eyebrow="Evidence-backed alignment"
          tag="strengths_json"
          items={report.strengths_json ?? []}
          empty="No strengths returned for this report."
        />
        <ReportListCard
          title="Gaps"
          eyebrow="Highest leverage improvements"
          tag="gaps_json"
          items={report.gaps_json ?? []}
          empty="No gaps returned for this report."
          danger
        />
        <ReportListCard
          title="Recommendations"
          eyebrow="Next resume edits"
          tag="recommendations_json"
          items={report.recommendations_json ?? []}
          empty="No recommendations returned for this report."
        />

        <article className="report-section-card source-trace-card">
          <header>
            <span className="mini-tag">Trace</span>
            <span className="code-chip">source records</span>
          </header>
          <h2>Source material</h2>
          <dl className="trace-list">
            <div>
              <dt>Resume</dt>
              <dd>{resume.title}</dd>
            </div>
            <div>
              <dt>Job</dt>
              <dd>
                {job.title ?? "Untitled role"} {job.company ? `· ${job.company}` : ""}
              </dd>
            </div>
            <div>
              <dt>Parse confidence</dt>
              <dd>
                Resume {formatPercent(resume.parse_confidence)} · Job {formatPercent(job.parse_confidence)}
              </dd>
            </div>
            <div>
              <dt>Session</dt>
              <dd>{report.session_id ?? resume.session_id ?? "anonymous"}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="report-wide-section" aria-labelledby="report-evidence-title">
        <div className="section-heading compact-heading">
          <div>
            <p className="eyebrow">Requirement-level evidence</p>
            <h2 id="report-evidence-title">Inspect exactly what matched and what did not.</h2>
          </div>
          <p>
            These rows come from the persisted match evidence table, so the score is not just a black
            box percentage.
          </p>
        </div>
        <div className="report-evidence-list">
          {report.evidence.map((item) => (
            <EvidenceCard item={item} key={item.id} />
          ))}
          {!report.evidence.length && <p className="empty-note">No evidence rows returned.</p>}
        </div>
      </section>

      <section className="report-wide-section" aria-labelledby="report-optimizer-title">
        <div className="section-heading compact-heading">
          <div>
            <p className="eyebrow">Truth-guarded optimizer</p>
            <h2 id="report-optimizer-title">Rewrite suggestions with guardrail status.</h2>
          </div>
          <p>
            Suggestions are useful only when they stay grounded in the source resume. Risky claims are
            explicitly flagged for review.
          </p>
        </div>
        <div className="report-suggestion-grid">
          {optimization.suggestions.map((suggestion) => (
            <SuggestionCard key={suggestion.id} suggestion={suggestion} />
          ))}
          {!optimization.suggestions.length && <p className="empty-note">No suggestions returned.</p>}
        </div>
      </section>
    </>
  );
}

function MetricTile({ label, value, compact = false }: { label: string; value: string; compact?: boolean }) {
  return (
    <div className={compact ? "report-metric-tile compact" : "report-metric-tile"}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function KeywordCloud({
  title,
  keywords,
  tone,
}: {
  title: string;
  keywords: string[];
  tone: "success" | "danger";
}) {
  return (
    <div className="keyword-cloud-block">
      <h3>{title}</h3>
      <div className="keyword-cloud">
        {(keywords.length ? keywords : ["No keywords returned"]).map((keyword) => (
          <span className={`keyword-chip ${tone}`} key={`${title}-${keyword}`}>
            {keyword}
          </span>
        ))}
      </div>
    </div>
  );
}

function InlineWarnings({ warnings }: { warnings: string[] }) {
  return (
    <div className="inline-warning-list">
      <strong>Warnings</strong>
      <ul>
        {warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
    </div>
  );
}

function ReportListCard({
  title,
  eyebrow,
  tag,
  items,
  empty,
  danger = false,
}: {
  title: string;
  eyebrow: string;
  tag: string;
  items: string[];
  empty: string;
  danger?: boolean;
}) {
  return (
    <article className={danger ? "report-section-card danger-list-card" : "report-section-card"}>
      <header>
        <span className="mini-tag">{eyebrow}</span>
        <span className="code-chip">{tag}</span>
      </header>
      <h2>{title}</h2>
      <ul className={danger ? "gap-list" : "strength-list"}>
        {(items.length ? items : [empty]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}

function TruthGuardWarning({ suggestions }: { suggestions: RewriteSuggestion[] }) {
  return (
    <section className="truth-warning-panel" aria-labelledby="truth-warning-title">
      <span className="status-pill warning">Review recommended</span>
      <div>
        <h2 id="truth-warning-title">Some rewrite suggestions need human review.</h2>
        <p>
          {suggestions.length} suggestion{suggestions.length === 1 ? "" : "s"} include guardrail
          warnings. Keep them as drafts until the claims are verified against the original resume.
        </p>
      </div>
    </section>
  );
}

function EvidenceCard({ item }: { item: MatchEvidence }) {
  return (
    <article className="report-evidence-card">
      <header>
        <span className={`status-pill ${statusTone(item.match_status)}`}>{item.match_status}</span>
        <span className="code-chip">{item.match_type}</span>
        <span className="code-chip">confidence {formatPercent(item.confidence)}</span>
      </header>
      <h3>{item.job_requirement_text}</h3>
      <p>{item.resume_evidence_text ?? item.explanation ?? "No direct resume evidence found."}</p>
      {item.explanation && item.resume_evidence_text && <small>{item.explanation}</small>}
    </article>
  );
}

function SuggestionCard({ suggestion }: { suggestion: RewriteSuggestion }) {
  return (
    <article className="report-suggestion-card">
      <header>
        <span className={`status-pill ${truthStatusClass(suggestion.truth_status)}`}>
          {suggestion.truth_status}
        </span>
        <span className="code-chip">+{suggestion.estimated_score_lift ?? 0} pts</span>
      </header>
      <h3>{humanize(suggestion.section_type)}</h3>
      {suggestion.original_text && (
        <blockquote>
          <span>Original</span>
          {suggestion.original_text}
        </blockquote>
      )}
      <p>{suggestion.suggested_text}</p>
      {suggestion.reason && <small>{suggestion.reason}</small>}
      {suggestion.guardrail_reason && <small className="guardrail-note">{suggestion.guardrail_reason}</small>}
    </article>
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

function readStringArray(source: Record<string, unknown> | null, key: string): string[] {
  const value = source?.[key];
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function buildMarkdownReport(bundle: ReportBundle, reportUrl: string): string {
  const { report, resume, job, optimization } = bundle;
  const matchedKeywords = readStringArray(report.ats_report_json, "keywords_matched");
  const missingKeywords = readStringArray(report.ats_report_json, "keywords_missing");
  const lines = [
    `# JobFit AI Match Report`,
    "",
    `- Report: ${report.id}`,
    `- URL: ${reportUrl}`,
    `- Role: ${job.title ?? "Untitled role"}${job.company ? ` at ${job.company}` : ""}`,
    `- Resume: ${resume.title}`,
    `- Overall score: ${report.overall_score}%`,
    `- Analysis confidence: ${formatPercent(report.analysis_confidence)}`,
    `- Projected score: ${optimization.score_before ?? report.overall_score}% → ${optimization.score_after ?? report.overall_score}%`,
    "",
    "## Strengths",
    ...markdownList(report.strengths_json ?? []),
    "",
    "## Gaps",
    ...markdownList(report.gaps_json ?? []),
    "",
    "## Recommendations",
    ...markdownList(report.recommendations_json ?? []),
    "",
    "## ATS Keywords",
    `- Matched: ${matchedKeywords.join(", ") || "n/a"}`,
    `- Missing: ${missingKeywords.join(", ") || "n/a"}`,
    "",
    "## Evidence Rows",
    ...report.evidence.slice(0, 10).flatMap((item) => [
      `- ${item.match_status.toUpperCase()} · ${item.job_requirement_text}`,
      `  - Evidence: ${item.resume_evidence_text ?? item.explanation ?? "No direct evidence"}`,
    ]),
    "",
    "## Rewrite Suggestions",
    ...optimization.suggestions.flatMap((item) => [
      `- ${item.truth_status.toUpperCase()} · ${humanize(item.section_type)} · +${item.estimated_score_lift ?? 0} pts`,
      `  - ${item.suggested_text}`,
      item.guardrail_reason ? `  - Guardrail: ${item.guardrail_reason}` : "",
    ]),
    "",
  ];

  return lines.filter((line, index, array) => line !== "" || array[index - 1] !== "").join("\n");
}

function markdownList(items: string[]): string[] {
  return items.length ? items.map((item) => `- ${item}`) : ["- n/a"];
}

function scoreLabel(score: number): string {
  if (score >= 80) return "strong match";
  if (score >= 60) return "promising fit";
  return "limited fit";
}

function scoreTone(score: number): string {
  if (score >= 80) return "success";
  if (score >= 60) return "warning";
  return "danger";
}

function statusTone(status: string): string {
  if (status === "strong" || status === "partial") return "success";
  if (status === "weak") return "warning";
  return "danger";
}

function truthStatusClass(status: string): string {
  if (status === "safe") return "success";
  if (status === "needs_review") return "warning";
  return "danger";
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function formatPercent(value: number | null): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
