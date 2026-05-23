from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MetricEntry:
    name: str
    value: float
    display_value: str
    description: str


@dataclass(slots=True)
class ExampleEntry:
    example_id: str
    status: str
    summary: str
    details_json: dict[str, Any]


@dataclass(slots=True)
class TaskEvaluationReport:
    task_name: str
    display_name: str
    metrics: list[MetricEntry]
    examples: list[ExampleEntry]
    average_latency_ms: float

    def metrics_json(self) -> dict[str, float]:
        return {metric.name: metric.value for metric in self.metrics}


@dataclass(slots=True)
class EvaluationRunReport:
    requested_task: str
    dataset: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tasks: list[TaskEvaluationReport] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    report_path: Path | None = None
    persisted_run_id: str | None = None

    def summary_json(self) -> dict[str, Any]:
        return {
            "requested_task": self.requested_task,
            "dataset": self.dataset,
            "generated_at": self.generated_at.isoformat(),
            "warnings": self.warnings,
            "tasks": {
                task.task_name: {
                    "metrics": task.metrics_json(),
                    "average_latency_ms": task.average_latency_ms,
                    "example_count": len(task.examples),
                }
                for task in self.tasks
            },
        }
