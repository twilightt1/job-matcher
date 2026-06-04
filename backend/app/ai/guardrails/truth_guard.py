from __future__ import annotations

import json

from app.ai.clients.base import GuardResult, LLMUsage, TruthGuardClient
from app.ai.clients.openai_compat import OpenAICompatLLMClient
from app.ai.matching.normalization import extract_keywords, normalize_skill
from app.ai.prompt_loader import load_prompt_template
from app.ai.schemas import ResumeExtraction
from app.ai.schemas.optimization import RewriteSuggestionDraft
from app.ai.schemas.truth_guard import TruthGuardDecision
from app.core.config import Settings

TRUTH_GUARD_ENTAILMENT_PROMPT_NAME = "truth_guard_entailment.v1.md"

UNSUPPORTED_SIGNAL_TERMS = {
    "awarded",
    "founded",
    "increased",
    "led",
    "managed",
    "million",
    "owned",
    "reduced",
    "scaled",
}


class LLMTruthGuard(TruthGuardClient):
    """OpenAI-compatible entailment judge for rewrite truthfulness."""

    def __init__(self, settings: Settings) -> None:
        self._client = OpenAICompatLLMClient(settings)
        self.model_name = settings.llm_model

    async def evaluate(
        self,
        suggestion: RewriteSuggestionDraft,
        resume: ResumeExtraction,
    ) -> GuardResult:
        prompt = _build_entailment_prompt(suggestion, resume)
        decision, usage = await self._client.generate_structured(
            prompt=prompt,
            output_model=TruthGuardDecision,
        )
        return GuardResult(decision=decision, usage=usage)


class FallbackTruthGuard(TruthGuardClient):
    """Fail-safe wrapper that falls back to local truth checks on provider errors."""

    def __init__(self, primary: TruthGuardClient, fallback: TruthGuardClient) -> None:
        self._primary = primary
        self._fallback = fallback
        self.model_name = primary.model_name

    async def evaluate(
        self,
        suggestion: RewriteSuggestionDraft,
        resume: ResumeExtraction,
    ) -> GuardResult:
        try:
            return await self._primary.evaluate(suggestion, resume)
        except Exception:
            fallback_result = await self._fallback.evaluate(suggestion, resume)
            fallback_result.usage.metadata["fallback_from"] = self._primary.model_name
            return fallback_result


class LocalTruthGuard(TruthGuardClient):
    """Checks rewrite suggestions for unsupported claims against parsed resume evidence."""

    model_name = "local-truth-guard-v1"

    async def evaluate(
        self,
        suggestion: RewriteSuggestionDraft,
        resume: ResumeExtraction,
    ) -> GuardResult:
        resume_text = " ".join(
            [
                resume.summary or "",
                *resume.skills,
                *resume.experience_highlights,
                *resume.certifications,
            ]
        )
        resume_keywords = {normalize_skill(keyword) for keyword in extract_keywords(resume_text)}
        suggestion_keywords = {
            normalize_skill(keyword) for keyword in extract_keywords(suggestion.suggested_text)
        }
        original_keywords = extract_keywords(suggestion.original_text or "")
        keyword_claims = sorted(
            keyword
            for keyword in suggestion_keywords - resume_keywords
            if keyword not in original_keywords and len(keyword) > 3
        )
        unsupported_signals = sorted(
            term
            for term in UNSUPPORTED_SIGNAL_TERMS
            if term in suggestion_keywords - resume_keywords
        )
        new_claims = sorted(set(keyword_claims + unsupported_signals))[:8]

        if unsupported_signals:
            decision = TruthGuardDecision(
                truth_status="unsupported",
                new_claims=new_claims,
                reason=(
                    "Suggestion appears to introduce high-impact claims absent from "
                    "resume evidence."
                ),
                confidence=0.78,
            )
            return GuardResult(
                decision=decision,
                usage=LLMUsage(provider="local", model_name=self.model_name, latency_ms=0),
            )
        if new_claims:
            decision = TruthGuardDecision(
                truth_status="needs_review",
                new_claims=new_claims,
                reason="Suggestion adds wording not directly supported by parsed resume evidence.",
                confidence=0.66,
            )
            return GuardResult(
                decision=decision,
                usage=LLMUsage(provider="local", model_name=self.model_name, latency_ms=0),
            )
        decision = TruthGuardDecision(
            truth_status="safe",
            new_claims=[],
            reason="All important rewrite keywords are grounded in existing resume evidence.",
            confidence=0.86,
        )
        return GuardResult(
            decision=decision,
            usage=LLMUsage(provider="local", model_name=self.model_name, latency_ms=0),
        )


def _build_entailment_prompt(
    suggestion: RewriteSuggestionDraft,
    resume: ResumeExtraction,
) -> str:
    template = load_prompt_template(TRUTH_GUARD_ENTAILMENT_PROMPT_NAME)
    return template.replace(
        "<<<RESUME_JSON>>>",
        json.dumps(resume.model_dump(mode="json"), ensure_ascii=False),
    ).replace(
        "<<<SUGGESTION_JSON>>>",
        json.dumps(suggestion.model_dump(mode="json"), ensure_ascii=False),
    )
