from __future__ import annotations

from app.ai.clients.base import (
    JobParserClient,
    ResumeOptimizerClient,
    ResumeParserClient,
    TruthGuardClient,
)
from app.ai.clients.local_job_parser import LocalJobParserClient
from app.ai.clients.local_resume_optimizer import LocalResumeOptimizer
from app.ai.clients.local_resume_parser import LocalResumeParserClient
from app.ai.clients.openai_compat import OpenAICompatLLMClient
from app.ai.guardrails.truth_guard import FallbackTruthGuard, LLMTruthGuard, LocalTruthGuard
from app.core.config import Settings


def get_resume_parser_client(settings: Settings) -> ResumeParserClient:
    if settings.ai_provider == "openai":
        return OpenAICompatLLMClient(settings)
    return LocalResumeParserClient()


def get_job_parser_client(settings: Settings) -> JobParserClient:
    if settings.ai_provider == "openai":
        return OpenAICompatLLMClient(settings)
    return LocalJobParserClient()


def get_resume_optimizer_client(settings: Settings) -> ResumeOptimizerClient:
    if settings.ai_provider == "openai":
        return OpenAICompatLLMClient(settings)
    return LocalResumeOptimizer()


def get_truth_guard_client(settings: Settings) -> TruthGuardClient:
    if settings.ai_provider == "openai":
        try:
            return FallbackTruthGuard(LLMTruthGuard(settings), LocalTruthGuard())
        except Exception:
            return LocalTruthGuard()
    return LocalTruthGuard()
