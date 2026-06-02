from __future__ import annotations

from app.ai.clients.local_resume_parser import LocalResumeParserClient
from app.ai.languages import detect_supported_languages
from app.ai.schemas import JobExtraction, ResumeExtraction
from app.ai.scoring.match_engine import DeterministicMatchEngine


def test_detect_supported_languages_handles_four_target_languages_and_aliases() -> None:
    text = "English, tiếng Việt, Mandarin Chinese, and 日本語 communication required."

    assert detect_supported_languages(text) == [
        "English",
        "Vietnamese",
        "Chinese",
        "Japanese",
    ]


def test_local_resume_parser_extracts_four_target_languages() -> None:
    parser = LocalResumeParserClient()

    result = parser.parse_resume(
        "Alex Nguyen\n"
        "AI Platform Engineer\n"
        "Skills: Python, FastAPI\n"
        "Languages: English, Vietnamese, Chinese, Japanese\n"
        "- Built multilingual AI workflows.\n"
    )

    assert result.extraction.languages == [
        "English",
        "Vietnamese",
        "Chinese",
        "Japanese",
    ]


def test_match_engine_scores_chinese_and_japanese_language_requirements() -> None:
    engine = DeterministicMatchEngine()
    resume = ResumeExtraction(
        candidate_name="Alex Nguyen",
        skills=["Python"],
        experience_highlights=["Built Python APIs for regional AI products."],
        languages=["English", "Vietnamese", "Chinese", "Japanese"],
        total_years_experience=4,
    )
    job = JobExtraction(
        title="Regional AI Engineer",
        summary="Requires Chinese and Japanese communication for APAC stakeholders.",
        required_skills=["Python"],
        requirements=[],
    )

    result = engine.compute(resume, job)

    assert result.breakdown["languages"] == {
        "score": 100,
        "matched": ["Chinese", "Japanese"],
    }
    assert "Resume includes language coverage for Chinese, Japanese." in result.strengths
