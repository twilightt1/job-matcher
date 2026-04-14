export default function DiagnosticsPage() {
  return (
    <main className="page-shell compact-shell">
      <p className="eyebrow">AI Diagnostics</p>
      <h1>Model, prompt, and evaluation telemetry</h1>
      <p className="hero-text narrow">
        This portfolio-focused page will surface AI run logs, prompt versions, latency, token
        usage, validation status, semantic matches, and evaluation results.
      </p>

      <section className="pipeline-grid diagnostics-grid">
        {[
          "Prompt version tracking",
          "AIRun latency and cost",
          "JSON schema validation",
          "Embedding similarity evidence",
          "Truth guard decisions",
          "Eval metric snapshots",
        ].map((item) => (
          <div className="pipeline-card" key={item}>
            <span>AI</span>
            <p>{item}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
