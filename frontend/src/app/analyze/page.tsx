const scoreBreakdown = [
  { label: "Required skills", value: 92 },
  { label: "Requirement overlap", value: 78 },
  { label: "Experience fit", value: 74 },
  { label: "Language coverage", value: 100 },
];

const strengths = [
  "Strong Python and FastAPI alignment for backend API delivery.",
  "Evidence shows production support for ML inference workflows.",
  "Truth guard can safely surface matching skills already present in the resume.",
];

const gaps = [
  "PostgreSQL and vector-search experience should be emphasized more clearly.",
  "Cross-functional platform ownership needs stronger evidence in experience bullets.",
  "ATS keywords for observability and model monitoring are still underrepresented.",
];

const optimizerSuggestions = [
  {
    title: "Summary refinement",
    status: "safe",
    copy: "Reframe the opening summary around ML platform APIs and production inference support.",
  },
  {
    title: "Skills reprioritization",
    status: "needs_review",
    copy: "Move PostgreSQL-adjacent evidence higher if the resume already supports it through project history.",
  },
  {
    title: "Experience rewrite",
    status: "unsupported",
    copy: "Adding ownership language without explicit resume evidence would be blocked by the truth guard.",
  },
];

export default function AnalyzePage() {
  return (
    <main className="page-shell compact-shell">
      <nav className="topbar" aria-label="Analyze navigation">
        <div className="brand-group">
          <div className="brand-badge" aria-hidden="true">
            JF
          </div>
          <div className="brand-meta">
            <p className="brand-title">JobFit AI</p>
            <p className="brand-caption">Premium frontend MVP flow</p>
          </div>
        </div>
        <div className="nav-links">
          <a className="nav-link" href="/" id="analyze-home-link">
            Overview
          </a>
          <a className="nav-link" href="/diagnostics" id="analyze-diagnostics-link">
            Diagnostics
          </a>
        </div>
      </nav>

      <section className="page-intro">
        <p className="eyebrow">Frontend MVP Flow</p>
        <h1>Analyze resume-to-job fit with a report that feels premium and inspectable.</h1>
        <p className="supporting-copy">
          This interface demonstrates the ideal end-to-end user journey: paste inputs, generate a
          deterministic match report, inspect evidence, and review truth-guarded optimization
          suggestions in one polished workspace.
        </p>
        <div className="hero-actions">
          <button className="primary-button" id="generate-report-button" type="button">
            Generate AI Match Report
          </button>
          <button className="secondary-button" id="load-demo-data-button" type="button">
            Load Demo Scenario
          </button>
        </div>
      </section>

      <section className="analysis-grid" aria-label="Resume analysis workspace">
        <article className="analysis-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Inputs</p>
              <h2>Resume and job context</h2>
            </div>
            <p>
              The final backend integration will submit these inputs to parsing, matching, and
              optimization endpoints already implemented in FastAPI.
            </p>
          </div>

          <div className="form-grid">
            <div className="input-card">
              <label htmlFor="resume-textarea">
                Resume text
                <span className="hint">Parsed into structured candidate evidence</span>
              </label>
              <textarea
                id="resume-textarea"
                defaultValue="Senior backend engineer with Python, FastAPI, PostgreSQL, and ML inference API experience. Built internal tooling for model-serving workflows and collaborated with data teams on deployment reliability."
              />
            </div>

            <div className="input-card">
              <label htmlFor="job-textarea">
                Job description
                <span className="hint">Requirements, skills, and ATS signals</span>
              </label>
              <textarea
                id="job-textarea"
                defaultValue="We are hiring an ML Platform Engineer to build Python and FastAPI services, improve PostgreSQL-backed platform tooling, strengthen observability, and partner across data and product teams."
              />
            </div>
          </div>

          <div className="inline-metrics" aria-label="Workflow preview metrics">
            <div className="mini-metric">
              <strong>Parse → Score → Optimize</strong>
              <span>end-to-end workflow already implemented</span>
            </div>
            <div className="mini-metric">
              <strong>Structured JSON</strong>
              <span>resume/job schemas drive the pipeline</span>
            </div>
            <div className="mini-metric">
              <strong>Grounded rewrites</strong>
              <span>truth guard checks every suggestion</span>
            </div>
          </div>
        </article>

        <article className="report-panel">
          <div className="panel-label">
            <span>Preview report</span>
            <span className="score-pill status-pill success">84% strong fit</span>
          </div>
          <h2>Match report with evidence and optimization layers</h2>
          <p className="supporting-copy">
            The design below previews how the FastAPI scoring and optimization endpoints surface in
            a single recruiter-facing experience.
          </p>

          <div className="score-breakdown">
            {scoreBreakdown.map((item) => (
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
            <div className="insight-card">
              <header>
                <span className="mini-tag">Strengths</span>
                <span className="code-chip">explanation_json</span>
              </header>
              <h3>Why the candidate scores well</h3>
              <ul className="strength-list">
                {strengths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="evidence-card">
              <header>
                <span className="mini-tag">Gaps</span>
                <span className="code-chip">ats_report_json</span>
              </header>
              <h3>What the optimizer should address</h3>
              <ul className="gap-list">
                {gaps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="optimizer-grid">
            {optimizerSuggestions.map((suggestion) => (
              <article className="optimizer-card" key={suggestion.title}>
                <header>
                  <span className={`status-pill ${
                    suggestion.status === "safe"
                      ? "success"
                      : suggestion.status === "needs_review"
                        ? "warning"
                        : "danger"
                  }`}>
                    {suggestion.status}
                  </span>
                  <span className="code-chip">rewrite suggestion</span>
                </header>
                <h3>{suggestion.title}</h3>
                <p>{suggestion.copy}</p>
              </article>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
