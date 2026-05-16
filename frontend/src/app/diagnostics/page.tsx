const diagnosticsCards = [
  {
    tag: "Prompt versioning",
    title: "Track prompt and schema lineage",
    copy: "Every AI step captures prompt names, versions, schema revisions, and validation state for review.",
  },
  {
    tag: "AIRun telemetry",
    title: "Latency and token visibility are built in",
    copy: "The backend persists latency, token counts, providers, model names, and status transitions for each run.",
  },
  {
    tag: "Truth guard",
    title: "Unsupported resume claims are explicitly classified",
    copy: "Optimization suggestions are labeled safe, needs review, or unsupported before being exposed to the UI.",
  },
  {
    tag: "Deterministic evidence",
    title: "Scores can always be traced back to normalized signals",
    copy: "The dashboard explains missing skills, requirement overlap, ATS keywords, and supporting evidence objects.",
  },
  {
    tag: "Validation",
    title: "Schema repair and validation are first-class metrics",
    copy: "Malformed or suspicious model outputs are visible instead of being hidden behind opaque success states.",
  },
  {
    tag: "Evaluation ready",
    title: "The product is positioned for evals and offline benchmarks",
    copy: "Telemetry and structured outputs make it straightforward to compare prompts, models, and scoring revisions later.",
  },
];

const timeline = [
  {
    step: "01",
    title: "Input normalization",
    copy: "Resume and job text are converted into schema-validated JSON using traceable parse runs.",
  },
  {
    step: "02",
    title: "Scoring pipeline",
    copy: "Match reports store overall score, explanation JSON, ATS coverage, and evidence rows.",
  },
  {
    step: "03",
    title: "Optimization pipeline",
    copy: "Grounded rewrite drafts and truth-guard decisions are persisted with their own AI observability trail.",
  },
];

const telemetryPanels = [
  {
    title: "Latest session snapshot",
    badge: "session telemetry",
    items: [
      "resume_parse · success · local-resume-parser-v1",
      "job_parse · success · local-job-parser-v1",
      "resume_optimize · success · local-resume-optimizer-v1",
      "truth_guard · success · local-truth-guard-v1",
    ],
  },
  {
    title: "Visibility recruiters can understand",
    badge: "product narrative",
    items: [
      "Prompt version awareness",
      "Validation status surfaced to UI",
      "Evidence-backed explanation summaries",
      "Blocked unsupported rewrites",
    ],
  },
];

export default function DiagnosticsPage() {
  return (
    <main className="page-shell compact-shell">
      <nav className="topbar" aria-label="Diagnostics navigation">
        <div className="brand-group">
          <div className="brand-badge" aria-hidden="true">
            JF
          </div>
          <div className="brand-meta">
            <p className="brand-title">JobFit AI</p>
            <p className="brand-caption">AI observability and eval-readiness view</p>
          </div>
        </div>
        <div className="nav-links">
          <a className="nav-link" href="/" id="diagnostics-home-link">
            Overview
          </a>
          <a className="nav-link" href="/analyze" id="diagnostics-analyze-link">
            Analyze Flow
          </a>
        </div>
      </nav>

      <section className="page-intro">
        <p className="eyebrow">AI Diagnostics</p>
        <h1>Model, prompt, validation, and truth-guard telemetry in one dashboard.</h1>
        <p className="supporting-copy">
          This page turns backend observability into a premium portfolio surface: it showcases the
          discipline behind schema validation, prompt tracking, latency visibility, and grounded AI
          behavior instead of hiding those concerns behind a generic UX shell.
        </p>
        <div className="quick-links">
          <a className="ghost-button" href="/analyze" id="diagnostics-cta-analyze">
            Review the product flow
          </a>
          <a className="ghost-button" href="/" id="diagnostics-cta-home">
            Back to overview
          </a>
        </div>
      </section>

      <section className="diagnostics-grid" aria-label="Diagnostics capability cards">
        {diagnosticsCards.map((card) => (
          <article className="diagnostics-card" key={card.title}>
            <span className="card-tag">{card.tag}</span>
            <h3>{card.title}</h3>
            <p>{card.copy}</p>
          </article>
        ))}
      </section>

      <section className="telemetry-strip" aria-labelledby="telemetry-title">
        <div>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Execution trail</p>
              <h2 id="telemetry-title">A clean story from parse runs to guarded resume rewrites</h2>
            </div>
            <p>
              The interface is designed to make AI pipeline reliability legible to both technical
              reviewers and product-minded hiring managers.
            </p>
          </div>
          <div className="timeline-stack">
            {timeline.map((item) => (
              <article className="timeline-card" key={item.step}>
                <span className="timeline-step">Step {item.step}</span>
                <h3>{item.title}</h3>
                <p>{item.copy}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="telemetry-grid">
          {telemetryPanels.map((panel) => (
            <article className="telemetry-card" key={panel.title}>
              <header>
                <span className="mini-tag">{panel.badge}</span>
                <span className="code-chip">AIRun / AIOutput</span>
              </header>
              <h3>{panel.title}</h3>
              <ul className="telemetry-list">
                {panel.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
