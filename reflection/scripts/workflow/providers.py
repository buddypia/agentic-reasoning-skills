"""Provider adapters for structured LLM calls."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol

from .anthropic_utils import create_message_with_auto_max_tokens
from .raw import extract_response_meta, to_jsonable


@dataclass(slots=True)
class ProviderResponse:
    provider: str
    model: str
    request: dict[str, Any]
    response_text: str
    response_meta: dict[str, Any]
    parsed_output: Any | None = None


class ProviderAdapter(Protocol):
    name: str

    async def generate_structured(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        schema: dict[str, Any],
        schema_name: str,
        output_model: Any | None,
    ) -> ProviderResponse:
        raise NotImplementedError


def _extract_gemini_text(response: object) -> str:
    candidates = getattr(response, "candidates", None)
    parts_text: list[str] = []
    if candidates:
        for cand in candidates:
            content = getattr(cand, "content", None)
            if content is None and isinstance(cand, dict):
                content = cand.get("content")
            parts = getattr(content, "parts", None)
            if parts is None and isinstance(content, dict):
                parts = content.get("parts")
            if not parts:
                continue
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text is None and isinstance(part, dict):
                    part_text = part.get("text")
                if isinstance(part_text, str) and part_text:
                    parts_text.append(part_text)
    if parts_text:
        return "\n".join(parts_text).strip()
    text = getattr(response, "text", None)
    if isinstance(text, str) and text:
        return text
    return ""


class OpenAIAdapter:
    name = "openai"

    async def generate_structured(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        schema: dict[str, Any],
        schema_name: str,
        output_model: Any | None,
    ) -> ProviderResponse:
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package required. pip install openai") from exc

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        response_text = response.choices[0].message.content or ""
        request = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
        }
        return ProviderResponse(
            provider=self.name,
            model=model,
            request=to_jsonable(request),
            response_text=response_text,
            response_meta=extract_response_meta(response),
        )


class AnthropicAdapter:
    name = "anthropic"

    async def generate_structured(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        schema: dict[str, Any],
        schema_name: str,
        output_model: Any | None,
    ) -> ProviderResponse:
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY")
        if output_model is None:
            raise RuntimeError("Anthropic structured output requires output_model")

        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package required. pip install anthropic") from exc

        client = AsyncAnthropic(api_key=api_key)
        raw_request: dict[str, Any] = {
            "model": model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": temperature,
        }

        response, used_max_tokens = await create_message_with_auto_max_tokens(
            client.beta.messages.parse,
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            output_format=output_model,
            stream=False,
        )
        raw_request = {
            **raw_request,
            "max_tokens": used_max_tokens,
            "output_format": getattr(output_model, "__name__", "OutputModel"),
            "structured_output": True,
            "stream": False,
        }

        response_text = ""
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                response_text += text

        parsed_output = getattr(response, "parsed_output", None)
        return ProviderResponse(
            provider=self.name,
            model=model,
            request=to_jsonable(raw_request),
            response_text=response_text,
            response_meta=extract_response_meta(response),
            parsed_output=parsed_output,
        )


class GeminiAdapter:
    name = "gemini"

    async def generate_structured(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        schema: dict[str, Any],
        schema_name: str,
        output_model: Any | None,
    ) -> ProviderResponse:
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai package required. pip install google-genai") from exc

        client = genai.Client(api_key=api_key)
        config = {
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_json_schema": schema,
        }
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=full_prompt,
            config=config,
        )
        response_text = _extract_gemini_text(response)
        request = {"model": model, "contents": full_prompt, "config": config}
        return ProviderResponse(
            provider=self.name,
            model=model,
            request=to_jsonable(request),
            response_text=response_text,
            response_meta=extract_response_meta(response),
        )


class MockAdapter:
    name = "mock"

    async def generate_structured(
        self,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        schema: dict[str, Any],
        schema_name: str,
        output_model: Any | None,
    ) -> ProviderResponse:
        payload = _build_mock_payload(schema_name, user_prompt)
        response_text = json.dumps(payload, ensure_ascii=False)
        request = {
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature,
            "mock": True,
        }
        return ProviderResponse(
            provider=self.name,
            model=model,
            request=to_jsonable(request),
            response_text=response_text,
            response_meta={"mock": True},
        )


def _build_mock_payload(schema_name: str, user_prompt: str) -> dict[str, Any]:
    """Return deterministic payloads for contract tests."""
    if schema_name == "generator_output":
        return {
            "draft": "mock-draft",
            "key_points": ["mock-key-point"],
            "confidence": 0.5,
        }
    if schema_name == "critic_output":
        return {
            "strengths": ["mock-strength"],
            "weaknesses": ["mock-weakness"],
            "suggestions": ["mock-suggestion"],
            "overall_score": 5,
            "critical_issues": [],
        }
    if schema_name == "refiner_output":
        return {
            "final_content": "mock-final-content",
            "improvements_made": ["mock-improvement"],
            "quality_score": 7,
        }
    return {"message": f"mock-response for {schema_name}", "prompt": user_prompt}


def get_adapter(provider: str) -> ProviderAdapter:
    normalized = provider.strip().lower()
    if normalized == "mock":
        return MockAdapter()
    if normalized == "openai":
        return OpenAIAdapter()
    if normalized in {"anthropic", "claude"}:
        return AnthropicAdapter()
    if normalized == "gemini":
        return GeminiAdapter()
    raise ValueError(f"Unknown provider: {provider}")
