from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from docx import Document
from fastapi.testclient import TestClient

from app.services.ingestion.extractors import IngestionError, extract_docx_text, extract_txt_text


def _docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_txt_text_normalizes_and_validates() -> None:
    extracted = extract_txt_text(
        b"Senior Backend Engineer\n\nSkills: Python, FastAPI, PostgreSQL, Docker, APIs",
        filename="resume.txt",
        content_type="text/plain",
    )

    assert extracted.source_kind == "text"
    assert "Python" in extracted.text
    assert extracted.char_count >= 50


def test_extract_docx_text_reads_paragraphs() -> None:
    extracted = extract_docx_text(
        _docx_bytes("Job description requiring Python, FastAPI, PostgreSQL, Docker, and APIs."),
        filename="jd.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert extracted.source_kind == "docx"
    assert "FastAPI" in extracted.text


def test_extract_text_rejects_too_short_content() -> None:
    try:
        extract_txt_text(b"too short", filename="tiny.txt", content_type="text/plain")
    except IngestionError as exc:
        assert "too short" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("Expected short text extraction to fail")


def test_resume_upload_endpoint(client: TestClient) -> None:
    resume_record = SimpleNamespace(
        id="resume-upload-1",
        title="Uploaded Resume",
        source_type="text",
        original_file_url=None,
        original_file_key="storage/uploads/resumes/resume.txt",
        raw_text="Senior Backend Engineer with Python, FastAPI, PostgreSQL, Docker, and APIs.",
        session_id="session-upload",
        parse_status="pending",
        parse_confidence=None,
        parsed_json=None,
        created_at="2026-06-13T00:00:00Z",
        updated_at="2026-06-13T00:00:00Z",
    )

    with patch(
        "app.api.routes.resumes.create_resume_from_upload",
        new_callable=AsyncMock,
    ) as create_resume_from_upload:
        create_resume_from_upload.return_value = resume_record
        response = client.post(
            "/api/resumes/upload",
            data={"title": "Uploaded Resume", "session_id": "session-upload"},
            files={
                "file": (
                    "resume.txt",
                    b"Senior Backend Engineer with Python, FastAPI, PostgreSQL, Docker, and APIs.",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "resume-upload-1"
    assert payload["source_type"] == "text"
    assert payload["original_file_key"].endswith("resume.txt")


def test_job_url_endpoint(client: TestClient) -> None:
    job_record = SimpleNamespace(
        id="job-url-1",
        title="ML Platform Engineer",
        company="Acme AI",
        location=None,
        description="Job description requiring Python, FastAPI, PostgreSQL, Docker, and APIs.",
        status="saved",
        source_url="https://example.com/jobs/ml-platform-engineer",
        work_mode="unknown",
        employment_type="unknown",
        seniority="unknown",
        session_id="session-url",
        parse_status="pending",
        parse_confidence=None,
        parsed_json=None,
        created_at="2026-06-13T00:00:00Z",
        updated_at="2026-06-13T00:00:00Z",
    )

    with patch(
        "app.api.routes.jobs.create_job_from_url",
        new_callable=AsyncMock,
    ) as create_job_from_url:
        create_job_from_url.return_value = job_record
        response = client.post(
            "/api/jobs/from-url",
            json={
                "url": "https://example.com/jobs/ml-platform-engineer",
                "title": "ML Platform Engineer",
                "company": "Acme AI",
                "session_id": "session-url",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "job-url-1"
    assert payload["source_url"] == "https://example.com/jobs/ml-platform-engineer"


def test_analyze_endpoint_with_pasted_text(client: TestClient) -> None:
    now = datetime.now(UTC)
    resume_record = SimpleNamespace(
        id="resume-analyze-1",
        title="Pasted Resume",
        source_type="text",
        original_file_url=None,
        original_file_key=None,
        raw_text="Senior Backend Engineer with Python, FastAPI, PostgreSQL, Docker, and APIs.",
        session_id="session-analyze",
        parse_status="completed",
        parse_confidence=0.91,
        parsed_json={"skills": ["Python", "FastAPI"]},
        created_at=now,
        updated_at=now,
    )
    job_record = SimpleNamespace(
        id="job-analyze-1",
        title="ML Platform Engineer",
        company="Acme AI",
        location=None,
        description="Job description requiring Python, FastAPI, PostgreSQL, Docker, and APIs.",
        status="saved",
        source_url=None,
        work_mode="unknown",
        employment_type="unknown",
        seniority="unknown",
        session_id="session-analyze",
        parse_status="completed",
        parse_confidence=0.89,
        parsed_json={"required_skills": ["Python", "FastAPI"]},
        created_at=now,
        updated_at=now,
    )
    evidence = SimpleNamespace(
        id="evidence-1",
        requirement_id="skill:python",
        job_requirement_text="python",
        resume_section_id="skill:python",
        resume_section_type="skill",
        resume_evidence_text="python",
        match_type="exact",
        match_status="strong",
        similarity_score=1.0,
        confidence=0.82,
        explanation="Normalized skill match found for python.",
        metadata_json={"category": "skill"},
        created_at=now,
    )
    report_record = SimpleNamespace(
        id="report-analyze-1",
        user_id=None,
        session_id="session-analyze",
        resume_id="resume-analyze-1",
        job_id="job-analyze-1",
        overall_score=86,
        analysis_confidence=0.93,
        breakdown_json={"skills": {"score": 90}, "requirements": {"score": 80}},
        strengths_json=["Resume demonstrates python."],
        gaps_json=[],
        recommendations_json=["Add more impact metrics."],
        ats_report_json={"coverage_ratio": 0.9},
        explanation_json={"summary": "Strong deterministic fit."},
        model_metadata_json={"engine": "deterministic-v1"},
        created_at=now,
        updated_at=now,
        evidence=[evidence],
    )
    suggestion = SimpleNamespace(
        id="suggestion-1",
        optimized_resume_id="optimized-analyze-1",
        section_type="summary",
        target_location="summary",
        original_text="Backend engineer",
        suggested_text="Backend engineer with verified FastAPI platform experience.",
        user_edited_text=None,
        targeted_requirements=["FastAPI"],
        keywords_added=["FastAPI"],
        reason="Targets a required backend skill.",
        estimated_score_lift=4,
        truth_status="safe",
        new_claims_json=[],
        guardrail_reason="Grounded in original resume text.",
        decision="pending",
        accepted_by_user=False,
        generated_by_ai_run_id="truth-run-1",
        created_at=now,
        updated_at=now,
    )
    optimization_record = SimpleNamespace(
        id="optimized-analyze-1",
        user_id=None,
        session_id="session-analyze",
        resume_id="resume-analyze-1",
        job_id="job-analyze-1",
        match_report_id="report-analyze-1",
        version_name="Job-targeted draft",
        content_json={"summary": "Optimized summary"},
        score_before=86,
        score_after=90,
        status="draft",
        generated_by_ai_run_id="optimizer-run-1",
        created_at=now,
        updated_at=now,
        suggestions=[suggestion],
    )
    bundle = SimpleNamespace(
        resume=resume_record,
        job=job_record,
        match_report=report_record,
        optimization=optimization_record,
    )

    with (
        patch(
            "app.api.routes.analyze.create_resume_from_text",
            new_callable=AsyncMock,
        ) as create_resume,
        patch("app.api.routes.analyze.create_job_from_text", new_callable=AsyncMock) as create_job,
        patch("app.api.routes.analyze.run_analysis", new_callable=AsyncMock) as run_analysis,
    ):
        create_resume.return_value = resume_record
        create_job.return_value = job_record
        run_analysis.return_value = bundle
        response = client.post(
            "/api/analyze",
            data={
                "resume_text": resume_record.raw_text,
                "resume_title": "Pasted Resume",
                "job_input_type": "text",
                "job_text": job_record.description,
                "job_title": "ML Platform Engineer",
                "company": "Acme AI",
                "session_id": "session-analyze",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["match_report"]["overall_score"] == 86
    assert payload["optimization"]["suggestions"][0]["truth_status"] == "safe"
