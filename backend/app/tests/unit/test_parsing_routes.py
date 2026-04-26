from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

NOW = datetime(2026, 6, 13, 0, 0, tzinfo=UTC)


def test_resume_parse_flow(client: TestClient) -> None:
    resume_record = SimpleNamespace(
        id="resume-123",
        title="Senior Backend Resume",
        raw_text="Jane Doe\nSenior Backend Engineer\nSkills: Python, FastAPI\n",
        session_id="session-parse-1",
        parse_status="pending",
        parse_confidence=None,
        parsed_json=None,
        parse_warnings=None,
        parse_error=None,
        created_at=NOW,
        updated_at=NOW,
    )
    parsed_resume = SimpleNamespace(
        id="resume-123",
        title="Senior Backend Resume",
        raw_text="Jane Doe\nSenior Backend Engineer\nSkills: Python, FastAPI\n",
        session_id="session-parse-1",
        parse_status="completed",
        parse_confidence=0.88,
        parsed_json={
            "candidate_name": "Jane Doe",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        },
        parse_warnings=["No explicit certifications section detected."],
        parse_error=None,
        created_at=NOW,
        updated_at=NOW,
    )
    ai_run = SimpleNamespace(
        id="airun-1",
        task_type="resume_parse",
        status="success",
        provider="local",
        model_name="local-rule-parser-v1",
        prompt_name="resume_parser.v1.md",
        prompt_version="v1",
        schema_version="v1",
        validation_status="valid",
        latency_ms=1,
        created_at=NOW,
    )

    with (
        patch(
            "app.api.routes.resumes.create_resume",
            new_callable=AsyncMock,
        ) as create_resume,
        patch(
            "app.api.routes.resumes.get_resume",
            new_callable=AsyncMock,
        ) as get_resume,
        patch(
            "app.api.routes.resumes.parse_resume_record",
            new_callable=AsyncMock,
        ) as parse_resume_record,
        patch(
            "app.api.routes.resumes.list_ai_runs_for_session",
            new_callable=AsyncMock,
        ) as list_ai_runs,
    ):
        create_resume.return_value = resume_record
        get_resume.side_effect = [resume_record, parsed_resume, parsed_resume]
        parse_resume_record.return_value = parsed_resume
        list_ai_runs.return_value = [ai_run]

        create_response = client.post(
            "/api/resumes",
            json={
                "title": "Senior Backend Resume",
                "session_id": "session-parse-1",
                "raw_text": (
                    "Jane Doe\n"
                    "Senior Backend Engineer\n"
                    "Summary: Python engineer with 6 years building APIs.\n"
                    "Skills: Python, FastAPI, PostgreSQL, Docker\n"
                ),
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["id"] == "resume-123"

        parse_response = client.post("/api/resumes/resume-123/parse", json={})
        assert parse_response.status_code == 200
        payload = parse_response.json()
        assert payload["parse_status"] == "completed"
        assert payload["parsed_json"]["candidate_name"] == "Jane Doe"
        assert "Python" in payload["parsed_json"]["skills"]

        diagnostics_response = client.get("/api/resumes/resume-123/parse-diagnostics")
        assert diagnostics_response.status_code == 200
        diagnostics_payload = diagnostics_response.json()
        assert len(diagnostics_payload["ai_runs"]) == 1
        assert diagnostics_payload["ai_runs"][0]["task_type"] == "resume_parse"
        assert diagnostics_payload["ai_runs"][0]["status"] == "success"


def test_job_parse_flow(client: TestClient) -> None:
    job_record = SimpleNamespace(
        id="job-123",
        title="Senior ML Engineer",
        company="Acme AI",
        description="Senior ML Engineer\nCompany: Acme AI\nRequirements: Python\n",
        status="draft",
        session_id="session-parse-2",
        parse_status="pending",
        parse_confidence=None,
        parsed_json=None,
        parse_warnings=None,
        parse_error=None,
        created_at=NOW,
        updated_at=NOW,
    )
    parsed_job = SimpleNamespace(
        id="job-123",
        title="Senior ML Engineer",
        company="Acme AI",
        description="Senior ML Engineer\nCompany: Acme AI\nRequirements: Python\n",
        status="draft",
        session_id="session-parse-2",
        parse_status="completed",
        parse_confidence=0.9,
        parsed_json={
            "company": "Acme AI",
            "required_skills": ["Python", "Machine Learning", "FastAPI"],
        },
        parse_warnings=["No explicit location detected."],
        parse_error=None,
        created_at=NOW,
        updated_at=NOW,
    )
    ai_run = SimpleNamespace(
        id="airun-2",
        task_type="job_parse",
        status="success",
        provider="local",
        model_name="local-rule-parser-v1",
        prompt_name="job_parser.v1.md",
        prompt_version="v1",
        schema_version="v1",
        validation_status="valid",
        latency_ms=1,
        created_at=NOW,
    )

    with (
        patch(
            "app.api.routes.jobs.create_job",
            new_callable=AsyncMock,
        ) as create_job,
        patch(
            "app.api.routes.jobs.get_job",
            new_callable=AsyncMock,
        ) as get_job,
        patch(
            "app.api.routes.jobs.parse_job_record",
            new_callable=AsyncMock,
        ) as parse_job_record,
        patch(
            "app.api.routes.jobs.list_ai_runs_for_session",
            new_callable=AsyncMock,
        ) as list_ai_runs,
    ):
        create_job.return_value = job_record
        get_job.side_effect = [job_record, parsed_job, parsed_job]
        parse_job_record.return_value = parsed_job
        list_ai_runs.return_value = [ai_run]

        create_response = client.post(
            "/api/jobs",
            json={
                "title": "Senior ML Engineer",
                "company": "Acme AI",
                "session_id": "session-parse-2",
                "description": (
                    "Senior ML Engineer\n"
                    "Company: Acme AI\n"
                    "Requirements: Python, Machine Learning, FastAPI\n"
                ),
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["id"] == "job-123"

        parse_response = client.post("/api/jobs/job-123/parse", json={})
        assert parse_response.status_code == 200
        payload = parse_response.json()
        assert payload["parse_status"] == "completed"
        assert payload["parsed_json"]["company"] == "Acme AI"
        assert "Python" in payload["parsed_json"]["required_skills"]

        diagnostics_response = client.get("/api/jobs/job-123/parse-diagnostics")
        assert diagnostics_response.status_code == 200
        diagnostics_payload = diagnostics_response.json()
        assert len(diagnostics_payload["ai_runs"]) == 1
        assert diagnostics_payload["ai_runs"][0]["task_type"] == "job_parse"
        assert diagnostics_payload["ai_runs"][0]["status"] == "success"
