from __future__ import annotations

import re

from app.ai.clients.base import ParsedResumeResult, ResumeParserClient
from app.ai.schemas import ResumeContact, ResumeEducationItem, ResumeExtraction


class LocalResumeParserClient(ResumeParserClient):
    """Heuristic parser used for MVP development before remote LLM integration."""

    model_name = "local-rule-parser-v1"

    def parse_resume(self, raw_text: str) -> ParsedResumeResult:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        lower_text = raw_text.lower()

        candidate_name = lines[0] if lines else None
        headline = lines[1] if len(lines) > 1 else None
        summary = self._extract_summary(lines)
        skills = self._extract_skills(raw_text)
        experience_highlights = self._extract_experience_highlights(lines)
        education = self._extract_education(lines)
        contact = self._extract_contact(raw_text)
        languages = self._extract_languages(lower_text)
        certifications = self._extract_certifications(lines)
        years_experience = self._estimate_years_experience(lower_text)
        warnings = self._build_warnings(raw_text, skills, experience_highlights)

        extraction = ResumeExtraction(
            candidate_name=candidate_name,
            headline=headline,
            contact=contact,
            summary=summary,
            total_years_experience=years_experience,
            skills=skills,
            experience_highlights=experience_highlights,
            education=education,
            certifications=certifications,
            languages=languages,
        )

        confidence = max(
            0.45,
            min(
                0.92,
                0.52 + 0.04 * len(skills) + 0.03 * len(experience_highlights),
            ),
        )

        return ParsedResumeResult(
            extraction=extraction,
            confidence=round(confidence, 2),
            warnings=warnings,
            model_name=self.model_name,
        )

    def _extract_summary(self, lines: list[str]) -> str | None:
        for line in lines:
            lower_line = line.lower()
            if lower_line.startswith(("summary", "profile", "about")):
                return line.split(":", maxsplit=1)[-1].strip() or line
        return None

    def _extract_skills(self, raw_text: str) -> list[str]:
        patterns = [
            r"skills\s*[:\-]\s*(.+)",
            r"tech stack\s*[:\-]\s*(.+)",
            r"technologies\s*[:\-]\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text, flags=re.IGNORECASE)
            if match:
                return self._split_list(match.group(1))
        return []

    def _extract_experience_highlights(self, lines: list[str]) -> list[str]:
        bullets = [
            line.lstrip("-• ").strip()
            for line in lines
            if line.startswith(("-", "•"))
        ]
        return bullets[:6]

    def _extract_education(self, lines: list[str]) -> list[ResumeEducationItem]:
        education_items: list[ResumeEducationItem] = []
        keywords = ("university", "college", "bachelor", "master", "degree")
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                education_items.append(ResumeEducationItem(school=line))
        return education_items[:3]

    def _extract_contact(self, raw_text: str) -> ResumeContact:
        email_match = re.search(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            raw_text,
            flags=re.IGNORECASE,
        )
        phone_match = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", raw_text)
        linkedin_match = re.search(
            r"https?://(?:www\.)?linkedin\.com/\S+",
            raw_text,
            flags=re.IGNORECASE,
        )
        github_match = re.search(
            r"https?://(?:www\.)?github\.com/\S+",
            raw_text,
            flags=re.IGNORECASE,
        )

        return ResumeContact(
            email=email_match.group(0) if email_match else None,
            phone=phone_match.group(0) if phone_match else None,
            linkedin=linkedin_match.group(0) if linkedin_match else None,
            github=github_match.group(0) if github_match else None,
        )

    def _extract_languages(self, lower_text: str) -> list[str]:
        known_languages = ["english", "vietnamese", "japanese", "french", "german"]
        return [language.title() for language in known_languages if language in lower_text]

    def _extract_certifications(self, lines: list[str]) -> list[str]:
        certifications: list[str] = []
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ("certified", "certificate", "aws ", "gcp ")
            ):
                certifications.append(line)
        return certifications[:5]

    def _estimate_years_experience(self, lower_text: str) -> float | None:
        match = re.search(r"(\d+(?:\.\d+)?)\+?\s+years?", lower_text)
        if not match:
            return None
        return float(match.group(1))

    def _build_warnings(
        self,
        raw_text: str,
        skills: list[str],
        experience_highlights: list[str],
    ) -> list[str]:
        warnings: list[str] = []
        if len(raw_text.strip()) < 120:
            warnings.append("Resume text is short; extraction confidence may be limited.")
        if not skills:
            warnings.append("No explicit skills section detected.")
        if not experience_highlights:
            warnings.append("No bullet-style experience highlights detected.")
        return warnings

    def _split_list(self, value: str) -> list[str]:
        parts = re.split(r"[,|/•]", value)
        return [part.strip() for part in parts if part.strip()]
