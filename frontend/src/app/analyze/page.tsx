export default function AnalyzePage() {
  return (
    <main className="page-shell compact-shell">
      <p className="eyebrow">MVP Flow</p>
      <h1>Analyze resume-job fit</h1>
      <p className="hero-text narrow">
        This page will connect to the FastAPI backend in the next milestone. It is structured
        around the final product flow: resume input, job input, match report, and optimizer.
      </p>

      <section className="analysis-grid">
        <div className="glass-card input-card">
          <label htmlFor="resume-text">Resume text</label>
          <textarea id="resume-text" placeholder="Paste resume text here..." />
        </div>
        <div className="glass-card input-card">
          <label htmlFor="job-description">Job description</label>
          <textarea id="job-description" placeholder="Paste job description here..." />
        </div>
      </section>

      <button className="primary-button wide" type="button">
        Generate AI Match Report
      </button>
    </main>
  );
}
