from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.clients.base import (
    JobParserClient,
    LLMUsage,
    OptimizeResult,
    ParsedJobResult,
    ParsedResumeResult,
    ResumeOptimizerClient,
    ResumeParserClient,
)
from app.ai.prompt_loader import load_prompt_template
from app.ai.schemas import JobExtraction, ResumeExtraction
from app.ai.schemas.optimization import OptimizedResumeDraft
from app.core.config import Settings

RESUME_PROMPT_NAME = "resume_parser.v1.md"
JOB_PROMPT_NAME = "job_parser.v1.md"
OPTIMIZER_PROMPT_NAME = "resume_optimizer.v1.md"
JSON_REPAIR_PROMPT_NAME = "json_repair.v1.md"

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(slots=True)
class ChatCompletionResult:
    content: str
    usage: LLMUsage


class OpenAICompatLLMClient(ResumeParserClient, JobParserClient, ResumeOptimizerClient):
    """OpenAI-compatible async client for structured extraction and optimization."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai.")
        self._settings = settings
        self.model_name = settings.llm_model
        self._base_url = settings.openai_base_url.rstrip("/")
        self._chat_completions_url = f"{self._base_url}/chat/completions"
        self._headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

    async def parse_resume(self, raw_text: str) -> ParsedResumeResult:
        prompt_template = load_prompt_template(RESUME_PROMPT_NAME)
        prompt = prompt_template.replace("<<<RESUME_TEXT>>>", raw_text)
        content, usage, repaired = await self._generate_structured_content(
            prompt=prompt,
            output_model=ResumeExtraction,
        )
        extraction = self._validate_output(ResumeExtraction, content)
        warnings = ["Output required JSON repair before schema validation."] if repaired else []
        return ParsedResumeResult(
            extraction=extraction,
            confidence=0.82 if not repaired else 0.74,
            warnings=warnings,
            model_name=self.model_name,
            usage=usage,
        )

    async def parse_job(self, description: str) -> ParsedJobResult:
        prompt_template = load_prompt_template(JOB_PROMPT_NAME)
        prompt = prompt_template.replace("<<<JOB_DESCRIPTION>>>", description)
        content, usage, repaired = await self._generate_structured_content(
            prompt=prompt,
            output_model=JobExtraction,
        )
        extraction = self._validate_output(JobExtraction, content)
        warnings = ["Output required JSON repair before schema validation."] if repaired else []
        return ParsedJobResult(
            extraction=extraction,
            confidence=0.82 if not repaired else 0.74,
            warnings=warnings,
            model_name=self.model_name,
            usage=usage,
        )

    async def generate_structured(
        self,
        *,
        prompt: str,
        output_model: type[ModelT],
    ) -> tuple[ModelT, LLMUsage]:
        content, usage, _repaired = await self._generate_structured_content(
            prompt=prompt,
            output_model=output_model,
        )
        return self._validate_output(output_model, content), usage

    async def optimize(
        self,
        resume: ResumeExtraction,
        job: JobExtraction,
        match_report: dict[str, object],
    ) -> OptimizeResult:
        prompt_template = load_prompt_template(OPTIMIZER_PROMPT_NAME)
        prompt = (
            prompt_template.replace(
                "<<<RESUME_JSON>>>",
                json.dumps(resume.model_dump(mode="json")),
            )
            .replace("<<<JOB_JSON>>>", json.dumps(job.model_dump(mode="json")))
            .replace("<<<MATCH_ANALYSIS_JSON>>>", json.dumps(match_report))
        )
        content, usage, _repaired = await self._generate_structured_content(
            prompt=prompt,
            output_model=OptimizedResumeDraft,
        )
        draft = self._validate_output(OptimizedResumeDraft, content)
        return OptimizeResult(draft=draft, usage=usage)

    async def _generate_structured_content(
        self,
        *,
        prompt: str,
        output_model: type[ModelT],
    ) -> tuple[str, LLMUsage, bool]:
        completion = await self._chat(prompt)
        try:
            self._validate_output(output_model, completion.content)
            return completion.content, completion.usage, False
        except ValidationError as exc:
            if self._settings.llm_max_repair_attempts <= 0:
                raise ValueError(
                    "Model output failed schema validation and repair is disabled."
                ) from exc

            repair_prompt = self._build_repair_prompt(
                schema=output_model.model_json_schema(),
                invalid_text=completion.content,
                validation_errors=list(exc.errors()),
            )
            repaired_completion = await self._chat(repair_prompt)
            try:
                self._validate_output(output_model, repaired_completion.content)
            except ValidationError as repair_exc:
                raise ValueError(
                    "Model output could not be repaired to match the schema."
                ) from repair_exc
            repaired_usage = LLMUsage(
                latency_ms=repaired_completion.usage.latency_ms,
                input_token_count=repaired_completion.usage.input_token_count,
                output_token_count=repaired_completion.usage.output_token_count,
                total_token_count=repaired_completion.usage.total_token_count,
                repair_attempted=True,
                provider=repaired_completion.usage.provider,
                model_name=repaired_completion.usage.model_name,
                metadata={
                    **repaired_completion.usage.metadata,
                    "repair_prompt_used": True,
                },
            )
            return repaired_completion.content, repaired_usage, True

    async def _chat(self, prompt: str) -> ChatCompletionResult:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._settings.llm_temperature,
            "response_format": {"type": "json_object"},
        }
        started_at = perf_counter()
        async with httpx.AsyncClient(
            timeout=self._settings.llm_request_timeout_seconds,
        ) as client:
            response = await client.post(
                self._chat_completions_url,
                json=payload,
                headers=self._headers,
            )
        latency_ms = max(0, round((perf_counter() - started_at) * 1000))
        response.raise_for_status()
        response_json = response.json()
        content = self._extract_message_content(response_json)
        usage_json = response_json.get("usage") if isinstance(response_json, dict) else None
        usage = LLMUsage(
            latency_ms=latency_ms,
            input_token_count=self._usage_value(usage_json, "prompt_tokens"),
            output_token_count=self._usage_value(usage_json, "completion_tokens"),
            total_token_count=self._usage_value(usage_json, "total_tokens"),
            repair_attempted=False,
            provider="openai",
            model_name=self.model_name,
        )
        return ChatCompletionResult(content=content, usage=usage)

    def _extract_message_content(self, response_json: dict[str, Any]) -> str:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Chat completion response did not include any choices.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("Chat completion choice payload was not an object.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ValueError("Chat completion response did not include a message object.")
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Chat completion message content was not a string.")
        return self._strip_code_fences(content)

    def _validate_output(self, output_model: type[ModelT], content: str) -> ModelT:
        payload = json.loads(content)
        return output_model.model_validate(payload)

    def _build_repair_prompt(
        self,
        *,
        schema: dict[str, Any],
        invalid_text: str,
        validation_errors: list[Any],
    ) -> str:
        template = load_prompt_template(JSON_REPAIR_PROMPT_NAME)
        return (
            template.replace("<<<SCHEMA>>>", json.dumps(schema, ensure_ascii=False, indent=2))
            .replace("<<<INVALID_JSON_OR_TEXT>>>", invalid_text)
            .replace(
                "<<<VALIDATION_ERRORS>>>",
                json.dumps(validation_errors, ensure_ascii=False, indent=2),
            )
        )

    def _usage_value(self, usage_json: object, key: str) -> int | None:
        if not isinstance(usage_json, dict):
            return None
        value = usage_json.get(key)
        return value if isinstance(value, int) else None

    def _strip_code_fences(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```") and stripped.endswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 2:
                stripped = "\n".join(lines[1:-1]).strip()
        return stripped
