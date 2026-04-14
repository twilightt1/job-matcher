const pipelineSteps = [
  "LLM resume parsing",
  "Job requirement extraction",
  "Skill normalization",
  "Embedding evidence retrieval",
  "Explainable scoring",
  "Truth-guarded optimization",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">AI/ML Engineer Portfolio Project</p>
          <h1>Match resumes to jobs with explainable AI.</h1>
          <p className="hero-text">
            JobFit AI combines schema-first LLM extraction, semantic embeddings,
            deterministic scoring, and resume truth guardrails in one polished product demo.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="/analyze">
              Analyze a Resume
            </a>
            <a className="secondary-button" href="/diagnostics">
              View AI Diagnostics
            </a>
          </div>
        </div>

        <div className="glass-card score-card" aria-label="AI match report preview">
          <div className="score-orb">81%</div>
          <p className="card-kicker">Strong Match</p>
          <h2>Frontend Engineer · React + TypeScript</h2>
          <div className="score-bars">
            <span style={{ width: "84%" }}>Required skills</span>
            <span style={{ width: "79%" }}>Semantic experience</span>
            <span style={{ width: "72%" }}>ATS keywords</span>
          </div>
        </div>
      </section>

      <section className="pipeline-section" aria-labelledby="pipeline-title">
        <p className="eyebrow">Pipeline</p>
        <h2 id="pipeline-title">Built to show real AI engineering depth</h2>
        <div className="pipeline-grid">
          {pipelineSteps.map((step, index) => (
            <div className="pipeline-card" key={step}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{step}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
