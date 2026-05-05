from __future__ import annotations

from app.ai.matching.normalization import extract_keywords, normalize_skill
from app.ai.schemas import ResumeExtraction
from app.ai.schemas.optimization import RewriteSuggestionDraft
from app.ai.schemas.truth_guard import TruthGuardDecision

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


class LocalTruthGuard:
    """Checks rewrite suggestions for unsupported claims against parsed resume evidence."""

    model_name = "local-truth-guard-v1"

    def evaluate(
        self,
        suggestion: RewriteSuggestionDraft,
        resume: ResumeExtraction,
    ) -> TruthGuardDecision:
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
            return TruthGuardDecision(
                truth_status="unsupported",
                new_claims=new_claims,
                reason=(
                    "Suggestion appears to introduce high-impact claims absent from "
                    "resume evidence."
                ),
                confidence=0.78,
            )
        if new_claims:
            return TruthGuardDecision(
                truth_status="needs_review",
                new_claims=new_claims,
                reason="Suggestion adds wording not directly supported by parsed resume evidence.",
                confidence=0.66,
            )
        return TruthGuardDecision(
            truth_status="safe",
            new_claims=[],
            reason="All important rewrite keywords are grounded in existing resume evidence.",
            confidence=0.86,
        )
