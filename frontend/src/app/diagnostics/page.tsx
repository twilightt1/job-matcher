const diagnosticsCards = [
  {
    tag: "Prompt lineage",
    title: "Versioned prompts and schemas",
    copy: "Each AI-adjacent step records prompt names, prompt versions, schema versions, and validation state.",
  },
  {
    tag: "AIRun trail",
    title: "Runs are inspectable",
    copy: "Parse, optimize, and truth-guard operations persist status, provider, model, timing, and output metadata.",
  },
  {
    tag: "Truth guard",
    title: "Unsafe claims are flagged",
    copy: "Rewrite suggestions are classified before display so unsupported resume claims do not slip through silently.",
  },
  {
    tag: "Evidence rows",
    title: "Scores point to real signals",
    copy: "Match reports store requirement-level evidence, similarity signals, and explanation text for review.",
  },
  {
    tag: "Validation",
    title: "Structured outputs stay accountable",
    copy: "AI outputs are stored with validation status, warnings, and repair-ready metadata hooks.",
  },
  {
    tag: "Evals",
    title: "Benchmarks are ready to expand",
    copy: "The evaluation harness can compare parser, matching, and truth-guard behavior across datasets.",
  },
];

const timeline = [
  {
    step: "01",
    title: "Parse inputs",
    copy: "Resume and job text become schema-first JSON with parse confidence and warnings.",
  },
  {
    step: "02",
    title: "Create match report",
    copy: "The scoring engine writes breakdown JSON, ATS coverage, gaps, and evidence rows.",
  },
  {
    step: "03",
    title: "Generate optimizer draft",
    copy: "The optimizer proposes targeted resume changes based on the parsed job and match report.",
  },
  {
    step: "04",
    title: "Guard every suggestion",
    copy: "Truth-guard runs classify each rewrite as safe, needs review, or unsupported.",
  },
];

const telemetryPanels = [
  {
    title: "Latest session snapshot",
    badge: "runtime trace",
    items: [
      "resume_parse · success · local-resume-parser-v1",
      "job_parse · success · local-job-parser-v1",
      "resume_optimize · success · local-resume-optimizer-v1",
      "truth_guard · success · local-truth-guard-v1",
    ],
  },
  {
    title: "What reviewers can verify",
    badge: "portfolio signal",
    items: [
      "Schema-first extraction contracts",
      "Stored prompt and model metadata",
      "Evidence-backed score decomposition",
      "Explicit unsupported-claim detection",
    ],
  },
];

export default function DiagnosticsPage() {
  return (
    <main className="page-shell compact-shell diagnostics-shell">
      <nav className="topbar" aria-label="Diagnostics navigation">
        <a className="brand-group" href="/" id="diagnostics-home-brand">
          <span className="brand-badge" aria-hidden="true">
            JF
          </span>
          <span className="brand-meta">
            <span className="brand-title">JobFit AI</span>
            <span className="brand-caption">Observability console</span>
          </span>
        </a>
        <div className="nav-links">
          <a className="nav-link" href="/" id="diagnostics-home-link">
            Overview
          </a>
          <a className="nav-link" href="/analyze" id="diagnostics-analyze-link">
            Analyze
          </a>
        </div>
      </nav>

      <section className="page-intro diagnostics-hero" aria-labelledby="diagnostics-title">
        <p className="eyebrow">AI diagnostics</p>
        <h1 id="diagnostics-title">A clean control room for prompts, schemas, and truth guard runs.</h1>
        <p className="supporting-copy">
          This console reframes backend telemetry as a product feature: visible model runs,
          validation signals, evidence records, and safety decisions in a calm review surface.
        </p>
        <div className="quick-links">
          <a className="primary-button" href="/analyze" id="diagnostics-cta-analyze">
            Run the analyze flow
          </a>
          <a className="secondary-button" href="/" id="diagnostics-cta-home">
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
        <div className="telemetry-left">
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">Execution trail</p>
              <h2 id="telemetry-title">From input parsing to guarded rewrite decisions.</h2>
            </div>
            <p>
              The system is structured so each AI operation can be inspected, compared, and improved
              without losing the product story.
            </p>
          </div>
          <div className="timeline-stack">
            {timeline.map((item) => (
              <article className="timeline-card" key={item.step}>
                <span className="timeline-step">{item.step}</span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.copy}</p>
                </div>
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
