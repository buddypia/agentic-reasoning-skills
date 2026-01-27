"""Criticエージェント - ドラフトをレビュー・批評。"""

import json
import time
from copy import deepcopy
from typing import Any, Final

from .engine import Executor, WorkflowContext, handler
from .config import AgentConfig
from .prompts import get_prompt
from .providers import get_adapter
from .raw import to_jsonable
from .types import (
    GeneratorOutput,
    CriticOutput,
    StageRawData,
    CRITIC_JSON_SCHEMA,
)


CRITIC_SYSTEM_PROMPT: Final[str] = get_prompt("critic")


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    cleaned = cleaned.strip("`").strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    return cleaned


def _gemini_requires_property_ordering(model_id: str | None) -> bool:
    model = (model_id or "").lower()
    return any(token in model for token in ("gemini-2", "gemini-3"))


def _apply_property_ordering(schema: dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        return
    schema_type = schema.get("type")
    if schema_type == "object" or (isinstance(schema_type, list) and "object" in schema_type):
        props = schema.get("properties")
        if isinstance(props, dict):
            schema.setdefault("propertyOrdering", list(props.keys()))
            for prop_schema in props.values():
                if isinstance(prop_schema, dict):
                    _apply_property_ordering(prop_schema)
    items = schema.get("items")
    if isinstance(items, dict):
        _apply_property_ordering(items)


def _build_gemini_schema(model_id: str | None) -> dict[str, Any]:
    schema = deepcopy(CRITIC_JSON_SCHEMA)
    if _gemini_requires_property_ordering(model_id):
        _apply_property_ordering(schema)
    return schema


class CriticExecutor(Executor):
    """ドラフトをレビュー・批評する。"""

    def __init__(self, config: AgentConfig):
        super().__init__(id="critic_executor")
        self.config = config

    @handler
    async def critique(self, generator_output: GeneratorOutput, ctx: WorkflowContext[CriticOutput]) -> None:
        started = time.perf_counter()

        await ctx.set_shared_state("critic_model", self.config.model)

        original_prompt = await ctx.get_shared_state("original_prompt") or ""

        raw: StageRawData | None = None
        try:
            result = await self._call_critic_with_raw(original_prompt, generator_output)
        except Exception as exc:
            parsed = CriticOutput(
                strengths=["評価できません（エラー）"],
                weaknesses=[f"批評中にエラーが発生しました: {exc}"],
                suggestions=["再試行してください"],
                overall_score=5,
                critical_issues=["エラーが発生"],
            )
            raw = StageRawData(
                provider=self.config.normalized_provider(),
                model=self.config.model,
                system_prompt=CRITIC_SYSTEM_PROMPT,
                user_prompt=None,
                request=to_jsonable({"temperature": self.config.temperature}),
                parsed_output=parsed.model_dump(),
                error=str(exc),
            )
            result = parsed
        else:
            result, raw = result

        duration = time.perf_counter() - started

        await ctx.set_shared_state("critic_output", result.model_dump())
        await ctx.set_shared_state("critic_duration", duration)
        if raw is not None:
            raw.duration_sec = duration
            await ctx.set_shared_state("critic_raw", raw.model_dump())

        await ctx.send_message(result)

    async def _call_critic_with_raw(
        self, original_prompt: str, gen_output: GeneratorOutput
    ) -> tuple[CriticOutput, StageRawData]:
        provider = self.config.normalized_provider()
        adapter = get_adapter(provider)

        critique_prompt = (
            f"元の依頼:\n{original_prompt}\n\n"
            f"レビュー対象のドラフト:\n{gen_output.draft}\n\n"
            "主張されているキーポイント:\n"
            f"{json.dumps(gen_output.key_points, ensure_ascii=False, indent=2)}\n\n"
            f"Generatorの確信度: {gen_output.confidence}\n\n"
            "このドラフトを徹底的にレビューし、改善点を提示してください。"
        )

        schema = CRITIC_JSON_SCHEMA
        if provider == "gemini":
            schema = _build_gemini_schema(self.config.model)

        response = await adapter.generate_structured(
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=critique_prompt,
            temperature=self.config.temperature,
            schema=schema,
            schema_name="critic_output",
            output_model=CriticOutput,
        )

        raw = StageRawData(
            provider=provider,
            model=self.config.model,
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=critique_prompt,
            request=response.request,
            response_text=response.response_text,
            response_meta=response.response_meta,
        )

        parsed_output = response.parsed_output
        if parsed_output is not None:
            if not isinstance(parsed_output, CriticOutput):
                raise ValueError("Anthropic structured output missing for CriticOutput")
            parsed = parsed_output
        else:
            parsed = self._parse_response(response.response_text)

        raw.parsed_output = parsed.model_dump()
        return parsed, raw

    def _parse_response(self, text: str) -> CriticOutput:
        cleaned = _strip_code_fences(text)
        try:
            return CriticOutput.model_validate_json(cleaned)
        except Exception:
            try:
                data = json.loads(cleaned)
                return CriticOutput(
                    strengths=data.get("strengths", []),
                    weaknesses=data.get("weaknesses", []),
                    suggestions=data.get("suggestions", []),
                    overall_score=int(data.get("overall_score", 5)),
                    critical_issues=data.get("critical_issues", []),
                )
            except Exception:
                return CriticOutput(
                    strengths=["構造化レスポンスを解析できませんでした"],
                    weaknesses=["レスポンス形式に問題があります"],
                    suggestions=[cleaned[:500] if cleaned else "レスポンスが空です"],
                    overall_score=5,
                    critical_issues=[],
                )
