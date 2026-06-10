from __future__ import annotations

from pathlib import Path

from app.evals.types import EvaluationRunReport

REPORTS_DIR = Path(__file__).resolve().parents[3] / "artifacts" / "eval_reports"


def render_markdown_report(report: EvaluationRunReport) -> str:
    total_examples = sum(len(task.examples) for task in report.tasks)
    judge_enabled = any(
        "llm_judge" in example.details_json
        for task in report.tasks
        for example in task.examples
    )
    lines: list[str] = [
        f"# Evaluation Report ({report.dataset})",
        "",
        f"- Requested task: `{report.requested_task}`",
        f"- Generated at: `{report.generated_at.isoformat()}`",
        f"- Persisted run id: `{report.persisted_run_id or 'not_persisted'}`",
        f"- Evaluated examples: `{total_examples}`",
        f"- LLM judge enabled: `{judge_enabled}`",
    ]
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)

    for task in report.tasks:
        lines.extend(
            [
                "",
                f"## {task.display_name}",
                "",
                f"Average latency: `{task.average_latency_ms:.2f} ms`",
                "",
                "| Metric | Value | Description |",
                "| --- | --- | --- |",
            ]
        )
        lines.extend(
            f"| `{metric.name}` | `{metric.display_value}` | {metric.description} |"
            for metric in task.metrics
        )

        lines.extend(["", "### Example outcomes", ""])
        for example in task.examples:
            lines.append(
                f"- **{example.example_id}** — `{example.status}` — {example.summary}"
            )

    lines.append("")
    return "\n".join(lines)


def write_markdown_report(report: EvaluationRunReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"eval_report_{report.dataset}.md"
    output_path.write_text(render_markdown_report(report), encoding="utf-8")
    return output_path
