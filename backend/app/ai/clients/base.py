from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.ai.schemas import JobExtraction, ResumeExtraction
from app.ai.schemas.optimization import OptimizedResumeDraft, RewriteSuggestionDraft
from app.ai.schemas.truth_guard import TruthGuardDecision


@dataclass(slots=True)
class ParsedResumeResult:
    extraction: ResumeExtraction
    confidence: float
    warnings: list[str]
    model_name: str
    usage: LLMUsage


@dataclass(slots=True)
class ParsedJobResult:
    extraction: JobExtraction
    confidence: float
    warnings: list[str]
    model_name: str
    usage: LLMUsage


@dataclass(slots=True)
class LLMUsage:
    """Token and latency telemetry captured from a real model call.

    Local/heuristic clients populate ``latency_ms`` from a wall-clock measurement and
    leave the token counts at ``None``; OpenAI-compatible clients fill all fields from
    the provider's ``usage`` response.
    """

    latency_ms: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    total_token_count: int | None = None
    repair_attempted: bool = False
    provider: str = "local"
    model_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OptimizeResult:
    draft: OptimizedResumeDraft
    usage: LLMUsage


@dataclass(slots=True)
class GuardResult:
    decision: TruthGuardDecision
    usage: LLMUsage


class ResumeParserClient(Protocol):
    """Async parser protocol. Implementations may be local heuristics or LLM-backed."""

    model_name: str

    async def parse_resume(self, raw_text: str) -> ParsedResumeResult: ...


class JobParserClient(Protocol):
    """Async parser protocol. Implementations may be local heuristics or LLM-backed."""

    model_name: str

    async def parse_job(self, description: str) -> ParsedJobResult: ...


class ResumeOptimizerClient(Protocol):
    """Async optimizer protocol producing grounded rewrite suggestions."""

    model_name: str

    async def optimize(
        self,
        resume: ResumeExtraction,
        job: JobExtraction,
        match_report: dict[str, object],
    ) -> OptimizeResult: ...


class TruthGuardClient(Protocol):
    """Async truth-guard protocol classifying rewrite safety against resume evidence."""

    model_name: str

    async def evaluate(
        self,
        suggestion: RewriteSuggestionDraft,
        resume: ResumeExtraction,
    ) -> GuardResult: ...
