const pipelineSteps = [
  {
    tag: "01",
    title: "Structured extraction",
    copy: "Resume and job text are normalized into schema-first JSON for reliable downstream scoring.",
  },
  {
    tag: "02",
    title: "Deterministic evidence",
    copy: "Skill aliases, requirement overlap, language checks, and confidence signals stay inspectable.",
  },
  {
    tag: "03",
    title: "Truth-guarded optimization",
    copy: "Rewrite suggestions are generated, checked for unsupported claims, and tracked with AI runs.",
  },
];

const metrics = [
  { label: "Backend milestones", value: "4 / 7", detail: "Parsing, scoring, optimizer, truth guard" },
  { label: "Verified backend tests", value: "11", detail: "Type-safe and passing in .venv" },
  { label: "AI telemetry layers", value: "3", detail: "AIRun, AIOutput, diagnostics dashboard" },
  { label: "Portfolio narrative", value: "End-to-end", detail: "From raw text to explainable optimization" },
];

const highlights = [
  {
    tag: "Explainable scoring",
    title: "Built for recruiter trust, not black-box magic",
    copy: "Every score is decomposed into skills, requirement evidence, experience fit, and language coverage.",
  },
  {
    tag: "Grounded optimization",
    title: "Resume rewrites stay anchored to verified evidence",
    copy: "Truth guard decisions classify suggestions as safe, needs review, or unsupported before they ever reach the user.",
  },
  {
    tag: "AI observability",
    title: "Prompt, schema, and latency telemetry are first-class",
    copy: "The product doubles as an AI engineering portfolio by exposing prompt versions, validation status, and model metadata.",
  },
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <nav className="topbar" aria-label="Primary navigation">
        <div className="brand-group">
          <div className="brand-badge" aria-hidden="true">
            JF
          </div>
          <div className="brand-meta">
            <p className="brand-title">JobFit AI</p>
            <p className="brand-caption">Portfolio-grade AI/ML product system</p>
          </div>
        </div>
        <div className="nav-links">
          <a className="nav-link" href="/analyze" id="nav-analyze-link">
            Analyze Flow
          </a>
          <a className="nav-link" href="/diagnostics" id="nav-diagnostics-link">
            Diagnostics
          </a>
        </div>
      </nav>

      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">AI/ML Engineer Portfolio Project</p>
          <h1>Explainable job matching with truth-guarded resume optimization.</h1>
          <p className="hero-text">
            JobFit AI combines schema-first parsing, deterministic evidence scoring, and grounded
            rewrite generation into a polished product demo that shows real AI engineering depth.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="/analyze" id="hero-analyze-button">
              Explore the MVP Flow
            </a>
            <a className="secondary-button" href="/diagnostics" id="hero-diagnostics-button">
              Review AI Telemetry
            </a>
          </div>
          <div className="stats-grid" aria-label="Project quick stats">
            <div className="stat-card">
              <strong>81%</strong>
              <span>example match confidence preview</span>
            </div>
            <div className="stat-card">
              <strong>safe / review / block</strong>
              <span>truth-guard decision layers</span>
            </div>
            <div className="stat-card">
              <strong>LLM + rules + evals</strong>
              <span>hybrid AI engineering stack</span>
            </div>
          </div>
        </div>

        <div className="hero-panel" aria-label="AI match report overview">
          <div className="panel-label">
            <span>Live report composition</span>
            <span className="signal-pill">Strong candidate fit</span>
          </div>
          <div className="orb-panel">
            <div className="score-orb">
              <span className="score-value">84%</span>
            </div>
            <div className="score-copy">
              <h2>ML Platform Engineer · Python + FastAPI</h2>
              <p>
                Deterministic evidence shows strong skill coverage, production API experience, and
                clear opportunities for truth-guarded resume tailoring.
              </p>
            </div>
          </div>
          <div className="inline-metrics">
            <div className="mini-metric">
              <strong>92</strong>
              <span>required skill coverage</span>
            </div>
            <div className="mini-metric">
              <strong>76</strong>
              <span>requirement overlap</span>
            </div>
            <div className="mini-metric">
              <strong>3</strong>
              <span>guarded rewrites suggested</span>
            </div>
          </div>
        </div>
      </section>

      <section className="section-block" aria-labelledby="metrics-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Why this project matters</p>
            <h2 id="metrics-title">A portfolio piece that proves product, backend, and AI rigor</h2>
          </div>
          <p>
            The UI is intentionally positioned as a polished narrative around the backend system:
            parsing, scoring, optimization, observability, and evaluation readiness.
          </p>
        </div>
        <div className="metrics-grid">
          {metrics.map((metric) => (
            <article className="metric-card" key={metric.label}>
              <span className="metric-tag">Snapshot</span>
              <strong className="kpi-value">{metric.value}</strong>
              <span className="kpi-label">{metric.label}</span>
              <p>{metric.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block" aria-labelledby="pipeline-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">System pipeline</p>
            <h2 id="pipeline-title">From raw text to accountable optimization</h2>
          </div>
          <p>
            The MVP flow is built to visualize how an AI/ML engineer structures a production-minded
            pipeline, not just a single prompt call.
          </p>
        </div>
        <div className="pipeline-grid">
          {pipelineSteps.map((step) => (
            <article className="pipeline-card" key={step.title}>
              <span className="timeline-step">{step.tag}</span>
              <strong>{step.title}</strong>
              <p>{step.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block" aria-labelledby="highlights-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Architecture highlights</p>
            <h2 id="highlights-title">Each feature tells a stronger engineering story</h2>
          </div>
          <p>
            This frontend is tuned to spotlight the exact backend capabilities that recruiters or
            hiring managers would expect in an AI product portfolio.
          </p>
        </div>
        <div className="highlights-grid">
          {highlights.map((highlight) => (
            <article className="highlight-card" key={highlight.title}>
              <span className="card-tag">{highlight.tag}</span>
              <h3>{highlight.title}</h3>
              <p>{highlight.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <p className="footer-note">
        Next step: use the Analyze Flow to preview how parsed inputs, scores, evidence, and
        optimizer outputs come together in one premium interface.
      </p>
    </main>
  );
}
