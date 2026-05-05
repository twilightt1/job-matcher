from __future__ import annotations

from app.ai.matching.normalization import extract_keywords, normalize_skill, normalize_skill_list
from app.ai.schemas import JobExtraction, ResumeExtraction
from app.ai.schemas.optimization import OptimizedResumeDraft, RewriteSuggestionDraft

MAX_SUGGESTIONS = 5


class LocalResumeOptimizer:
    """Grounded local optimizer used for the MVP before provider-backed LLM calls."""

    model_name = "local-resume-optimizer-v1"

    def optimize(
        self,
        resume: ResumeExtraction,
        job: JobExtraction,
        match_report: dict[str, object],
    ) -> OptimizedResumeDraft:
        missing_skills = _missing_skills(match_report)
        normalized_resume_skills = normalize_skill_list(resume.skills)
        suggestions: list[RewriteSuggestionDraft] = []

        summary_suggestion = self._summary_suggestion(resume, job, missing_skills)
        if summary_suggestion is not None:
            suggestions.append(summary_suggestion)

        skill_suggestion = self._skill_suggestion(missing_skills, normalized_resume_skills)
        if skill_suggestion is not None:
            suggestions.append(skill_suggestion)

        suggestions.extend(
            self._experience_suggestions(
                resume,
                job,
                missing_skills,
                remaining_slots=MAX_SUGGESTIONS - len(suggestions),
            )
        )
        suggestions = suggestions[:MAX_SUGGESTIONS]

        optimized_skills = _merge_skills(normalized_resume_skills, suggestions)
        projected_score = _projected_score(match_report, suggestions)

        return OptimizedResumeDraft(
            version_name="Targeted resume draft",
            summary=self._optimized_summary(resume, job, missing_skills),
            skills=optimized_skills,
            experience_highlights=list(resume.experience_highlights),
            suggestions=suggestions,
            projected_score=projected_score,
        )

    def _summary_suggestion(
        self,
        resume: ResumeExtraction,
        job: JobExtraction,
        missing_skills: list[str],
    ) -> RewriteSuggestionDraft | None:
        if not resume.summary:
            return None

        job_focus = job.title or "the target role"
        safe_keywords = _supported_keywords(missing_skills, resume)
        if not safe_keywords and job.title is None:
            return None

        keyword_text = ", ".join(safe_keywords[:3]) if safe_keywords else "relevant backend work"
        suggested_text = (
            f"{resume.summary.rstrip('.')} with targeted experience aligned to "
            f"{job_focus}, emphasizing {keyword_text}."
        )
        return RewriteSuggestionDraft(
            section_type="summary",
            target_location="professional_summary",
            original_text=resume.summary,
            suggested_text=suggested_text,
            targeted_requirements=safe_keywords,
            keywords_added=safe_keywords[:3],
            reason=(
                "Align the opening summary with the target job while reusing verified "
                "resume evidence."
            ),
            estimated_score_lift=5 if safe_keywords else 2,
        )

    def _skill_suggestion(
        self,
        missing_skills: list[str],
        normalized_resume_skills: list[str],
    ) -> RewriteSuggestionDraft | None:
        supported_missing = [skill for skill in missing_skills if skill in normalized_resume_skills]
        if not supported_missing:
            return None

        return RewriteSuggestionDraft(
            section_type="skills",
            target_location="skills",
            original_text=", ".join(normalized_resume_skills),
            suggested_text="Prioritize matching skills: " + ", ".join(supported_missing[:6]),
            targeted_requirements=supported_missing[:6],
            keywords_added=supported_missing[:6],
            reason="Surface existing skills that the target job explicitly asks for.",
            estimated_score_lift=min(10, 2 * len(supported_missing)),
        )

    def _experience_suggestions(
        self,
        resume: ResumeExtraction,
        job: JobExtraction,
        missing_skills: list[str],
        *,
        remaining_slots: int,
    ) -> list[RewriteSuggestionDraft]:
        suggestions: list[RewriteSuggestionDraft] = []
        if remaining_slots <= 0:
            return suggestions

        requirements = [item.requirement for item in job.requirements]
        for index, highlight in enumerate(resume.experience_highlights, start=1):
            if len(suggestions) >= remaining_slots:
                break
            matched_requirements = _overlapping_requirements(highlight, requirements)
            safe_keywords = _supported_keywords(missing_skills, resume, context=highlight)
            if not matched_requirements and not safe_keywords:
                continue

            keyword_clause = ""
            if safe_keywords:
                keyword_clause = " Highlight keywords: " + ", ".join(safe_keywords[:3]) + "."
            suggested_text = f"{highlight.rstrip('.')}.{keyword_clause}".strip()
            suggestions.append(
                RewriteSuggestionDraft(
                    section_type="experience",
                    target_location=f"experience_highlights[{index - 1}]",
                    original_text=highlight,
                    suggested_text=suggested_text,
                    targeted_requirements=matched_requirements[:3],
                    keywords_added=safe_keywords[:3],
                    reason=(
                        "Tie an existing experience bullet to job requirements without adding "
                        "new facts."
                    ),
                    estimated_score_lift=4 + min(4, len(matched_requirements)),
                )
            )

        return suggestions

    def _optimized_summary(
        self,
        resume: ResumeExtraction,
        job: JobExtraction,
        missing_skills: list[str],
    ) -> str | None:
        if not resume.summary:
            return None
        supported = _supported_keywords(missing_skills, resume)
        role = job.title or "target role"
        if not supported:
            return f"{resume.summary.rstrip('.')} aligned to the {role}."
        return (
            f"{resume.summary.rstrip('.')} aligned to the {role}, with emphasis on "
            f"{', '.join(supported[:3])}."
        )


def _missing_skills(match_report: dict[str, object]) -> list[str]:
    breakdown = match_report.get("breakdown_json")
    if isinstance(breakdown, dict):
        skills = breakdown.get("skills")
        if isinstance(skills, dict):
            missing = skills.get("missing")
            if isinstance(missing, list):
                return [normalize_skill(str(skill)) for skill in missing]

    ats_report = match_report.get("ats_report_json")
    if isinstance(ats_report, dict):
        missing = ats_report.get("keywords_missing")
        if isinstance(missing, list):
            return [normalize_skill(str(skill)) for skill in missing]

    return []


def _supported_keywords(
    keywords: list[str],
    resume: ResumeExtraction,
    *,
    context: str | None = None,
) -> list[str]:
    resume_skills = set(normalize_skill_list(resume.skills))
    searchable_text = " ".join([resume.summary or "", *resume.experience_highlights])
    if context is not None:
        searchable_text = context
    searchable_keywords = extract_keywords(searchable_text)

    supported: list[str] = []
    for keyword in keywords:
        normalized = normalize_skill(keyword)
        if normalized in resume_skills or normalized in searchable_keywords:
            supported.append(normalized)
    return supported


def _overlapping_requirements(highlight: str, requirements: list[str]) -> list[str]:
    highlight_keywords = extract_keywords(highlight)
    matched: list[str] = []
    for requirement in requirements:
        requirement_keywords = extract_keywords(requirement)
        if requirement_keywords and len(requirement_keywords & highlight_keywords) >= 2:
            matched.append(requirement)
    return matched


def _merge_skills(
    normalized_resume_skills: list[str],
    suggestions: list[RewriteSuggestionDraft],
) -> list[str]:
    merged = list(normalized_resume_skills)
    seen = set(merged)
    for suggestion in suggestions:
        for keyword in suggestion.keywords_added:
            normalized = normalize_skill(keyword)
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(normalized)
    return merged


def _projected_score(
    match_report: dict[str, object],
    suggestions: list[RewriteSuggestionDraft],
) -> int:
    base_score = match_report.get("overall_score")
    if not isinstance(base_score, int):
        base_score = 0
    estimated_lift = sum(suggestion.estimated_score_lift for suggestion in suggestions)
    return min(100, base_score + estimated_lift)
