const workflowSteps = [
  {
    step: "01",
    title: "Upload CV + JD",
    copy: "Bring a resume file, paste text, link a public JD, or upload a job document.",
  },
  {
    step: "02",
    title: "Extract & normalize",
    copy: "The backend converts files and web pages into clean, schema-ready text.",
  },
  {
    step: "03",
    title: "Score with evidence",
    copy: "Skills, requirements, experience, and language signals become explainable match rows.",
  },
  {
    step: "04",
    title: "Optimize safely",
    copy: "Rewrite suggestions are checked by the truth guard before they reach the UI.",
  },
];

const productCards = [
  {
    tag: "Ingestion",
    title: "PDF, DOCX, TXT, links — one clean intake layer",
    copy: "A single analyze flow accepts practical job-search inputs instead of forcing users into rigid forms.",
  },
  {
    tag: "Evidence",
    title: "Every score comes with a reason",
    copy: "The report stores requirement-level evidence so the user can see what matched and what is missing.",
  },
  {
    tag: "Optimization",
    title: "Resume rewrites without hallucinated claims",
    copy: "Suggestions are categorized as safe, needs review, or unsupported using parsed resume evidence.",
  },
  {
    tag: "Observability",
    title: "Built like an AI engineering system",
    copy: "Prompt names, schema versions, validation state, and run outputs are captured for diagnostics.",
  },
];

const resultPreview = [
  { label: "Skill coverage", value: "92", tone: "lime" },
  { label: "Requirement fit", value: "78", tone: "sky" },
  { label: "Truth-safe drafts", value: "3", tone: "coral" },
];

export default function HomePage() {
  return (
    <main className="page-shell landing-shell">
      <nav className="topbar" aria-label="Primary navigation">
        <a className="brand-group" href="/" id="nav-home-brand">
          <span className="brand-badge" aria-hidden="true">
            JF
          </span>
          <span className="brand-meta">
            <span className="brand-title">JobFit AI</span>
            <span className="brand-caption">AI resume match workspace</span>
          </span>
        </a>
        <div className="nav-links">
          <a className="nav-link" href="/analyze" id="nav-analyze-link">
            Analyze
          </a>
          <a className="nav-link" href="/diagnostics" id="nav-diagnostics-link">
            Diagnostics
          </a>
        </div>
      </nav>

      <section className="hero-grid landing-hero" aria-labelledby="home-hero-title">
        <div className="hero-copy">
          <p className="eyebrow">CV + Job Description → AI report</p>
          <h1 id="home-hero-title">A calmer, sharper way to prove job fit.</h1>
          <p className="hero-text">
            Upload a resume, add a job description, and JobFit AI turns the pair into an
            explainable match score, evidence-backed gaps, and truth-guarded resume improvements.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="/analyze" id="hero-analyze-button">
              Start AI analysis
            </a>
            <a className="secondary-button" href="/diagnostics" id="hero-diagnostics-button">
              View AI telemetry
            </a>
          </div>
          <div className="stats-grid" aria-label="Product capabilities">
            <div className="stat-card">
              <strong>PDF / DOCX / URL</strong>
              <span>real-world input sources</span>
            </div>
            <div className="stat-card">
              <strong>Evidence-first</strong>
              <span>no black-box scoring</span>
            </div>
            <div className="stat-card">
              <strong>Truth guard</strong>
              <span>safer rewrite suggestions</span>
            </div>
          </div>
        </div>

        <aside className="hero-panel report-mock" aria-label="Example match report preview">
          <div className="panel-label">
            <span>Live match preview</span>
            <span className="signal-pill">Portfolio demo</span>
          </div>
          <div className="mock-document-stack">
            <article className="mock-card resume-card">
              <span className="mini-tag">Resume</span>
              <h2>Senior Backend Engineer</h2>
              <p>Python · FastAPI · PostgreSQL · ML platform tooling</p>
            </article>
            <article className="mock-card jd-card">
              <span className="mini-tag">Target JD</span>
              <h2>ML Platform Engineer</h2>
              <p>Requires APIs, observability, data collaboration, and deployment reliability.</p>
            </article>
          </div>
          <div className="score-summary-card">
            <div className="score-orb">
              <span className="score-value">84%</span>
            </div>
            <div className="score-copy">
              <span className="mini-tag">Generated report</span>
              <h2>Strong evidence-backed fit</h2>
              <p>3 recommended rewrites, 2 missing skills, 4 stored evidence rows.</p>
            </div>
          </div>
          <div className="inline-metrics">
            {resultPreview.map((item) => (
              <div className={`mini-metric ${item.tone}`} key={item.label}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="section-block process-section" aria-labelledby="workflow-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">How it works</p>
            <h2 id="workflow-title">One workflow, four accountable AI steps.</h2>
          </div>
          <p>
            The product is designed for a clean demo: every stage is visible, inspectable, and tied
            to backend records rather than hidden behind a single magic button.
          </p>
        </div>
        <div className="pipeline-grid process-grid">
          {workflowSteps.map((step) => (
            <article className="pipeline-card process-card" key={step.title}>
              <span className="timeline-step">{step.step}</span>
              <strong>{step.title}</strong>
              <p>{step.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block" aria-labelledby="product-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">System highlights</p>
            <h2 id="product-title">A frontend that sells the engineering story.</h2>
          </div>
          <p>
            The redesign uses a bright bento layout and stronger hierarchy so the backend pipeline
            feels like a polished AI product, not a developer-only dashboard.
          </p>
        </div>
        <div className="highlights-grid bento-grid">
          {productCards.map((card) => (
            <article className="highlight-card bento-card" key={card.title}>
              <span className="card-tag">{card.tag}</span>
              <h3>{card.title}</h3>
              <p>{card.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cta-band" aria-labelledby="cta-title">
        <div>
          <p className="eyebrow">Ready for the live flow</p>
          <h2 id="cta-title">Try the complete CV/JD analysis pipeline.</h2>
          <p>
            Use the built-in demo text or upload real files to see extraction, matching, and guarded
            optimization in one workspace.
          </p>
        </div>
        <a className="primary-button dark-button" href="/analyze" id="bottom-analyze-button">
          Open Analyze Workbench
        </a>
      </section>
    </main>
  );
}
