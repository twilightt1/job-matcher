from __future__ import annotations

from typing import Any

import pytest

from app.ai.clients.base import GuardResult
from app.ai.clients.factory import get_truth_guard_client
from app.ai.clients.local_resume_optimizer import LocalResumeOptimizer
from app.ai.guardrails.truth_guard import FallbackTruthGuard, LLMTruthGuard, LocalTruthGuard
from app.ai.schemas import JobExtraction, JobRequirementItem, ResumeExtraction
from app.ai.schemas.optimization import RewriteSuggestionDraft

VALID_RESUME_JSON = """{
  "candidate_name": "Alex Nguyen",
  "headline": "AI Engineer",
  "contact": {},
  "summary": "Builds AI systems.",
  "total_years_experience": 4,
  "skills": ["Python"],
  "experience_highlights": ["Built ML APIs."],
  "education": [],
  "certifications": [],
  "languages": ["English"]
}"""

EMPTY_RESUME_JSON = """{
  "candidate_name": "Alex Nguyen",
  "headline": null,
  "contact": {},
  "summary": null,
  "total_years_experience": null,
  "skills": [],
  "experience_highlights": [],
  "education": [],
  "certifications": [],
  "languages": []
}"""


def usage_json(prompt: int, completion: int, total: int) -> dict[str, int]:
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


class FakeResponse:
    def __init__(self, content: str, usage: dict[str, int]) -> None:
        self._content = content
        self._usage = usage

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "choices": [{"message": {"content": self._content}}],
            "usage": self._usage,
        }


class RecordingAsyncClient:
    responses: list[FakeResponse] = []
    payloads: list[dict[str, object]] = []
    headers_list: list[dict[str, str]] = []
    timeouts: list[object] = []
    urls: list[str] = []

    def __init__(self, *_args: object, **kwargs: object) -> None:
        self.__class__.timeouts.append(kwargs.get("timeout"))

    async def __aenter__(self) -> RecordingAsyncClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(
        self,
        url: str,
        json: dict[str, object],
        headers: dict[str, str],
    ) -> FakeResponse:
        self.__class__.urls.append(url)
        self.__class__.payloads.append(json)
        self.__class__.headers_list.append(headers)
        if not self.__class__.responses:
            raise AssertionError("No fake responses configured")
        return self.__class__.responses.pop(0)

    @classmethod
    def reset(cls) -> None:
        cls.responses = []
        cls.payloads = []
        cls.headers_list = []
        cls.timeouts = []
        cls.urls = []


@pytest.fixture
def openai_client_module(monkeypatch: pytest.MonkeyPatch) -> Any:
    from app.ai.clients import openai_compat

    openai_client_module_any: Any = openai_compat
    RecordingAsyncClient.reset()
    monkeypatch.setattr(
        openai_client_module_any.httpx,
        "AsyncClient",
        RecordingAsyncClient,
    )
    return openai_client_module_any


def build_settings(**overrides: Any) -> Any:
    from app.core.config import Settings

    base: dict[str, Any] = {
        "AI_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "OPENAI_BASE_URL": "https://example.test/v1",
        "LLM_MODEL": "test-model",
        "LLM_TEMPERATURE": 0.0,
        "LLM_REQUEST_TIMEOUT_SECONDS": 30.0,
        "LLM_MAX_REPAIR_ATTEMPTS": 1,
    }
    base.update(overrides)
    return Settings(**base)


async def test_local_resume_optimizer_generates_grounded_suggestions() -> None:
    resume = ResumeExtraction(
        candidate_name="Jane Doe",
        summary="Backend engineer building Python APIs",
        skills=["Python", "FastAPI"],
        experience_highlights=["Built FastAPI services for ML inference."],
    )
    job = JobExtraction(
        title="ML Platform Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        requirements=[
            JobRequirementItem(
                requirement="Build FastAPI services for model inference.",
                requirement_type="required",
            )
        ],
    )
    match_report = {
        "overall_score": 72,
        "breakdown_json": {"skills": {"missing": ["FastAPI"]}},
    }

    result = await LocalResumeOptimizer().optimize(resume, job, match_report)

    assert result.draft.projected_score > 72
    assert result.draft.suggestions
    assert result.draft.suggestions[0].section_type == "summary"
    assert "fastapi" in result.draft.suggestions[0].keywords_added
    assert result.usage.provider == "local"


async def test_local_truth_guard_marks_supported_rewrite_safe() -> None:
    resume = ResumeExtraction(
        summary="Backend engineer building Python APIs",
        skills=["Python", "FastAPI"],
        experience_highlights=["Built FastAPI services for ML inference."],
    )
    suggestion = RewriteSuggestionDraft(
        section_type="experience",
        original_text="Built FastAPI services for ML inference.",
        suggested_text="Built FastAPI services for ML inference with Python APIs.",
        keywords_added=["fastapi", "python"],
        reason="Rephrase verified backend API evidence.",
        estimated_score_lift=4,
    )

    result = await LocalTruthGuard().evaluate(suggestion, resume)

    assert result.decision.truth_status == "safe"
    assert result.decision.new_claims == []
    assert result.usage.provider == "local"


async def test_local_truth_guard_flags_unsupported_claims() -> None:
    resume = ResumeExtraction(
        summary="Backend engineer building Python APIs",
        skills=["Python"],
        experience_highlights=["Built internal APIs."],
    )
    suggestion = RewriteSuggestionDraft(
        section_type="experience",
        original_text="Built internal APIs.",
        suggested_text="Led a team that increased revenue by millions using Kubernetes.",
        keywords_added=["leadership", "kubernetes"],
        reason="Add business impact.",
        estimated_score_lift=10,
    )

    result = await LocalTruthGuard().evaluate(suggestion, resume)

    assert result.decision.truth_status == "unsupported"
    assert "increased" in result.decision.new_claims or "led" in result.decision.new_claims
    assert result.usage.provider == "local"


async def test_openai_truth_guard_returns_structured_entailment_decision(
    openai_client_module: Any,
) -> None:
    RecordingAsyncClient.responses = [
        FakeResponse(
            """{
              "truth_status": "unsupported",
              "new_claims": ["kubernetes", "revenue"],
              "reason": "The resume does not support Kubernetes migration or revenue impact.",
              "confidence": 0.91
            }""",
            usage_json(20, 10, 30),
        )
    ]
    guard = LLMTruthGuard(build_settings())
    resume = ResumeExtraction(
        summary="Backend engineer building Python APIs",
        skills=["Python"],
        experience_highlights=["Built internal APIs."],
    )
    suggestion = RewriteSuggestionDraft(
        section_type="experience",
        original_text="Built internal APIs.",
        suggested_text="Led Kubernetes migration that increased revenue.",
        keywords_added=["kubernetes"],
        reason="Add stronger impact.",
        estimated_score_lift=10,
    )

    result = await guard.evaluate(suggestion, resume)

    assert result.decision.truth_status == "unsupported"
    assert result.decision.new_claims == ["kubernetes", "revenue"]
    assert result.usage.provider == "openai"
    assert result.usage.total_token_count == 30
    assert RecordingAsyncClient.payloads
    messages = RecordingAsyncClient.payloads[0]["messages"]
    assert isinstance(messages, list)
    assert "entailed" in messages[0]["content"].lower()


def test_truth_guard_factory_selects_openai_compatible_guard_with_fallback() -> None:
    guard = get_truth_guard_client(build_settings())

    assert isinstance(guard, FallbackTruthGuard)


def test_truth_guard_factory_falls_back_when_openai_guard_cannot_be_constructed() -> None:
    guard = get_truth_guard_client(build_settings(OPENAI_API_KEY=None))

    assert isinstance(guard, LocalTruthGuard)


async def test_fallback_truth_guard_uses_local_guard_when_primary_fails() -> None:
    class FailingTruthGuard:
        model_name = "failing-guard"

        async def evaluate(
            self,
            suggestion: RewriteSuggestionDraft,
            resume: ResumeExtraction,
        ) -> GuardResult:
            raise RuntimeError("provider unavailable")

    guard = FallbackTruthGuard(FailingTruthGuard(), LocalTruthGuard())
    result = await guard.evaluate(
        RewriteSuggestionDraft(
            section_type="experience",
            original_text="Built APIs.",
            suggested_text="Built APIs with Python.",
            keywords_added=["python"],
            reason="Grounded rewrite.",
            estimated_score_lift=2,
        ),
        ResumeExtraction(skills=["Python"], experience_highlights=["Built APIs."]),
    )

    assert result.usage.provider == "local"
    assert result.decision.truth_status == "safe"
    assert result.usage.metadata["fallback_from"] == "failing-guard"


async def test_local_usage_metadata_is_present() -> None:
    optimize_result = await LocalResumeOptimizer().optimize(
        ResumeExtraction(summary="Backend engineer", skills=["Python"]),
        JobExtraction(title="Backend Engineer"),
        {"overall_score": 10},
    )
    guard_result = await LocalTruthGuard().evaluate(
        RewriteSuggestionDraft(
            section_type="experience",
            original_text="Built APIs.",
            suggested_text="Built APIs with Python.",
            keywords_added=["python"],
            reason="Grounded rewrite.",
            estimated_score_lift=2,
        ),
        ResumeExtraction(skills=["Python"], experience_highlights=["Built APIs."]),
    )

    assert optimize_result.usage.model_name == LocalResumeOptimizer.model_name
    assert optimize_result.usage.repair_attempted is False
    assert guard_result.usage.model_name == LocalTruthGuard.model_name
    assert guard_result.usage.repair_attempted is False


async def test_openai_resume_parser_repairs_invalid_json(
    openai_client_module: Any,
) -> None:
    RecordingAsyncClient.responses = [
        FakeResponse('{"candidate_name": 42}', usage_json(10, 5, 15)),
        FakeResponse(VALID_RESUME_JSON, usage_json(12, 8, 20)),
    ]

    client = openai_client_module.OpenAICompatLLMClient(build_settings())
    result = await client.parse_resume("Alex Nguyen\nPython engineer")

    assert result.extraction.candidate_name == "Alex Nguyen"
    assert result.usage.provider == "openai"
    assert result.usage.repair_attempted is True
    assert result.usage.total_token_count == 20
    assert len(RecordingAsyncClient.payloads) == 2
    repair_messages = RecordingAsyncClient.payloads[1]["messages"]
    assert isinstance(repair_messages, list)
    assert "Validation errors:" in repair_messages[-1]["content"]
    assert any("repair" in warning.lower() for warning in result.warnings)


async def test_openai_resume_parser_raises_when_repair_exhausted(
    openai_client_module: Any,
) -> None:
    RecordingAsyncClient.responses = [
        FakeResponse('{"candidate_name": 42}', usage_json(10, 5, 15)),
        FakeResponse('{"candidate_name": 42}', usage_json(11, 6, 17)),
    ]

    client = openai_client_module.OpenAICompatLLMClient(build_settings())

    with pytest.raises(ValueError):
        await client.parse_resume("Alex Nguyen\nPython engineer")


async def test_openai_resume_parser_requires_api_key() -> None:
    from app.ai.clients.openai_compat import OpenAICompatLLMClient

    with pytest.raises(ValueError):
        OpenAICompatLLMClient(build_settings(OPENAI_API_KEY=None))


async def test_openai_resume_parser_emits_usage_metadata(
    openai_client_module: Any,
) -> None:
    RecordingAsyncClient.responses = [
        FakeResponse(VALID_RESUME_JSON, usage_json(11, 7, 18))
    ]

    client = openai_client_module.OpenAICompatLLMClient(build_settings())
    result = await client.parse_resume("Alex Nguyen\nPython engineer")

    assert result.usage.model_name == "test-model"
    assert result.usage.input_token_count == 11
    assert result.usage.output_token_count == 7
    assert result.usage.total_token_count == 18
    assert result.usage.latency_ms >= 0
    assert result.usage.repair_attempted is False
    assert result.extraction.skills == ["Python"]


async def test_openai_resume_parser_uses_configured_request_payload(
    openai_client_module: Any,
) -> None:
    RecordingAsyncClient.responses = [
        FakeResponse(EMPTY_RESUME_JSON, usage_json(3, 4, 7))
    ]

    client = openai_client_module.OpenAICompatLLMClient(
        build_settings(LLM_TEMPERATURE=0.3, LLM_REQUEST_TIMEOUT_SECONDS=12.5)
    )
    await client.parse_resume("Alex Nguyen\nPython engineer")

    payload = RecordingAsyncClient.payloads[0]
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["model"] == "test-model"
    assert payload["temperature"] == 0.3
    assert RecordingAsyncClient.timeouts[0] == 12.5
    assert RecordingAsyncClient.urls == ["https://example.test/v1/chat/completions"]
    assert RecordingAsyncClient.headers_list[0]["Authorization"] == "Bearer test-key"
    assert RecordingAsyncClient.headers_list[0]["Content-Type"] == "application/json"
    messages = payload["messages"]
    assert isinstance(messages, list)
    assert "Alex Nguyen" in messages[-1]["content"]
    assert "Python engineer" in messages[-1]["content"]


async def test_openai_resume_parser_accepts_code_fenced_json(
    openai_client_module: Any,
) -> None:
    RecordingAsyncClient.responses = [
        FakeResponse(f"```json\n{EMPTY_RESUME_JSON}\n```", usage_json(3, 4, 7))
    ]

    client = openai_client_module.OpenAICompatLLMClient(build_settings())
    result = await client.parse_resume("Alex Nguyen")

    assert result.extraction.candidate_name == "Alex Nguyen"
    assert result.warnings == []
    assert result.model_name == "test-model"
