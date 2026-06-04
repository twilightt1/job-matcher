from __future__ import annotations

import re

from app.ai.clients.base import JobParserClient, LLMUsage, ParsedJobResult
from app.ai.schemas import JobExtraction, JobRequirementItem


class LocalJobParserClient(JobParserClient):
    """Heuristic parser used as the offline fallback before remote LLM integration."""

    model_name = "local-rule-parser-v1"

    async def parse_job(self, description: str) -> ParsedJobResult:
        lines = [line.strip() for line in description.splitlines() if line.strip()]
        lower_text = description.lower()

        title = lines[0] if lines else None
        company = self._extract_company(lines)
        summary = self._extract_summary(lines)
        responsibilities = self._extract_bullets(lines)
        required_skills = self._extract_skills(
            description,
            section_names=("requirements", "required skills", "must have"),
        )
        preferred_skills = self._extract_skills(
            description,
            section_names=("nice to have", "preferred skills", "bonus"),
        )
        requirements = self._extract_requirements(lines)
        seniority = self._extract_seniority(lower_text)
        employment_type = self._extract_employment_type(lower_text)
        work_mode = self._extract_work_mode(lower_text)
        warnings = self._build_warnings(description, required_skills, requirements)

        extraction = JobExtraction(
            title=title,
            company=company,
            summary=summary,
            responsibilities=responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            requirements=requirements,
            seniority=seniority,
            employment_type=employment_type,
            work_mode=work_mode,
        )

        confidence = max(
            0.48,
            min(0.93, 0.54 + 0.05 * len(required_skills) + 0.02 * len(requirements)),
        )

        return ParsedJobResult(
            extraction=extraction,
            confidence=round(confidence, 2),
            warnings=warnings,
            model_name=self.model_name,
            usage=LLMUsage(provider="local", model_name=self.model_name, latency_ms=0),
        )

    def _extract_company(self, lines: list[str]) -> str | None:
        for line in lines[:4]:
            if line.lower().startswith("company"):
                return line.split(":", maxsplit=1)[-1].strip() or None
        return None

    def _extract_summary(self, lines: list[str]) -> str | None:
        for line in lines:
            if line.lower().startswith(("about the role", "summary", "overview")):
                return line.split(":", maxsplit=1)[-1].strip() or line
        return None

    def _extract_bullets(self, lines: list[str]) -> list[str]:
        bullets = [line.lstrip("-• ").strip() for line in lines if line.startswith(("-", "•"))]
        return bullets[:8]

    def _extract_skills(self, description: str, section_names: tuple[str, ...]) -> list[str]:
        for section_name in section_names:
            pattern = rf"{re.escape(section_name)}\s*[:\-]\s*(.+)"
            match = re.search(pattern, description, flags=re.IGNORECASE)
            if match:
                parts = re.split(r"[,|/•]", match.group(1))
                return [part.strip() for part in parts if part.strip()]
        return []

    def _extract_requirements(self, lines: list[str]) -> list[JobRequirementItem]:
        requirement_items: list[JobRequirementItem] = []
        for line in lines:
            lowered = line.lower()
            if line.startswith(("-", "•")) and any(
                keyword in lowered
                for keyword in (
                    "experience",
                    "skill",
                    "knowledge",
                    "proficient",
                    "ability",
                )
            ):
                text = line.lstrip("-• ").strip()
                requirement_items.append(
                    JobRequirementItem(requirement=text, evidence_text=text)
                )
        return requirement_items[:10]

    def _extract_seniority(self, lower_text: str) -> str | None:
        for level in ("intern", "junior", "mid", "senior", "lead", "manager"):
            if level in lower_text:
                return level
        return None

    def _extract_employment_type(self, lower_text: str) -> str | None:
        for employment_type in ("full-time", "part-time", "contract", "internship", "temporary"):
            if employment_type in lower_text:
                return employment_type.replace("-", "_")
        return None

    def _extract_work_mode(self, lower_text: str) -> str | None:
        if "hybrid" in lower_text:
            return "hybrid"
        if "remote" in lower_text:
            return "remote"
        if "onsite" in lower_text or "on-site" in lower_text:
            return "onsite"
        return None

    def _build_warnings(
        self,
        description: str,
        required_skills: list[str],
        requirements: list[JobRequirementItem],
    ) -> list[str]:
        warnings: list[str] = []
        if len(description.strip()) < 160:
            warnings.append("Job description is short; extraction confidence may be limited.")
        if not required_skills:
            warnings.append("No explicit required skills section detected.")
        if not requirements:
            warnings.append("No requirement bullets detected.")
        return warnings
