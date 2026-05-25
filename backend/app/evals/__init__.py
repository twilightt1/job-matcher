from __future__ import annotations

from typing import Any

__all__ = ["run_evaluation_task"]


def __getattr__(name: str) -> Any:
    if name == "run_evaluation_task":
        from app.evals.runner import run_evaluation_task

        return run_evaluation_task
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
