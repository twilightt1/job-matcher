from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.ai.schemas import JobExtraction, ResumeExtraction


@dataclass(slots=True)
class ParsedResumeResult:
    extraction: ResumeExtraction
    confidence: float
    warnings: list[str]
    model_name: str


@dataclass(slots=True)
class ParsedJobResult:
    extraction: JobExtraction
    confidence: float
    warnings: list[str]
    model_name: str


class ResumeParserClient(Protocol):
    def parse_resume(self, raw_text: str) -> ParsedResumeResult: ...


class JobParserClient(Protocol):
    def parse_job(self, description: str) -> ParsedJobResult: ...
