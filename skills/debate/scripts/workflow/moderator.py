"""Moderatorエージェント - 両視点を評価し最終判断を下す。"""

import json
import time
from copy import deepcopy
from typing import Any, Final

from .engine import Executor, WorkflowContext, handler

from .config import AgentConfig
from .providers import get_adapter
from .prompts import get_prompt
from .raw import to_jsonable
from .types import (
    OpponentOutput,
    ModeratorOutput,
    DebateResult,
    DebateRawData,
    StageRawData,
    MODERATOR_JSON_SCHEMA,
)

_MAX_OUTPUT_CHARS: Final[int] = 8000

MODERATOR_SYSTEM_PROMPT: Final[str] = get_prompt("moderator")


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    cleaned = cleaned.strip("`").strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    return cleaned


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


class ModeratorExecutor(Executor):
    """両視点を評価し最終判断を提供する。"""

    def __init__(self, config: AgentConfig):
        super().__init__(id="moderator_executor")
        self.config = config

    @handler
    async def evaluate(self, opponent_output: OpponentOutput, ctx: WorkflowContext[DebateResult]) -> None:
        started = time.perf_counter()

        await ctx.set_shared_state("moderator_model", self.config.model)

        original_topic = await ctx.get_shared_state("original_topic") or ""
        proponent_output = await ctx.get_shared_state("proponent_output") or {}
        proponent_duration = await ctx.get_shared_state("proponent_duration") or 0.0
        opponent_duration = await ctx.get_shared_state("opponent_duration") or 0.0

        raw: StageRawData | None = None
        try:
            result = await self._call_moderator_with_raw(original_topic, proponent_output, opponent_output)
        except Exception as exc:
            parsed = ModeratorOutput(
                summary=f"[Moderator: エラー（{exc}）]",
                proponent_score=5,
                opponent_score=5,
                key_insights=["エラーが発生"],
                final_verdict="エラーのため最終判断に到達できませんでした。",
                recommendation="再試行してください。",
                confidence=0.0,
            )
            raw = StageRawData(
                provider=self.config.normalized_provider(),
                model=self.config.model,
                system_prompt=MODERATOR_SYSTEM_PROMPT,
                user_prompt=original_topic,
                request=to_jsonable({"temperature": self.config.temperature}),
                parsed_output=parsed.model_dump(),
                error=str(exc),
            )
            result = parsed
        else:
            result, raw = result

        duration = time.perf_counter() - started
        total_duration = proponent_duration + opponent_duration + duration

        if raw is not None:
            raw.duration_sec = duration
            await ctx.set_shared_state("moderator_raw", raw.model_dump())

        # RAWデータの収集
        proponent_raw_data = await ctx.get_shared_state("proponent_raw")
        opponent_raw_data = await ctx.get_shared_state("opponent_raw")
        moderator_raw_data = raw.model_dump() if raw else None

        debate_raw: DebateRawData | None = None
        if proponent_raw_data or opponent_raw_data or moderator_raw_data:
            debate_raw = DebateRawData(
                proponent=StageRawData(**proponent_raw_data) if proponent_raw_data else None,
                opponent=StageRawData(**opponent_raw_data) if opponent_raw_data else None,
                moderator=StageRawData(**moderator_raw_data) if moderator_raw_data else None,
            )

        final_result = DebateResult(
            original_topic=original_topic,
            # Proponentデータ
            proponent_position=proponent_output.get("position", ""),
            proponent_arguments=proponent_output.get("arguments", []),
            proponent_evidence=proponent_output.get("evidence", []),
            proponent_benefits=proponent_output.get("benefits", []),
            proponent_confidence=proponent_output.get("confidence", 0.0),
            # Opponentデータ
            opponent_position=opponent_output.position,
            opponent_counter_arguments=opponent_output.counter_arguments,
            opponent_risks=opponent_output.risks,
            opponent_weaknesses=opponent_output.weaknesses,
            opponent_alternatives=opponent_output.alternatives,
            opponent_confidence=opponent_output.confidence,
            # Moderatorデータ
            debate_summary=result.summary,
            proponent_score=result.proponent_score,
            opponent_score=result.opponent_score,
            key_insights=result.key_insights,
            final_verdict=result.final_verdict,
            recommendation=result.recommendation,
            # メタデータ
            total_duration_sec=total_duration,
            proponent_model=await ctx.get_shared_state("proponent_model") or "",
            opponent_model=await ctx.get_shared_state("opponent_model") or "",
            moderator_model=self.config.model,
            # RAWデータ
            raw=debate_raw,
        )

        await ctx.yield_output(final_result)

    async def _call_moderator_with_raw(
        self,
        original_topic: str,
        proponent_output: dict,
        opponent_output: OpponentOutput,
    ) -> tuple[ModeratorOutput, StageRawData]:
        provider = self.config.normalized_provider()

        moderator_prompt = f"""討論テーマ:
{original_topic}

=== 賛成派（Proponent）の主張 ===

立場: {proponent_output.get('position', 'N/A')}

論拠:
{json.dumps(proponent_output.get('arguments', []), ensure_ascii=False, indent=2)}

根拠:
{json.dumps(proponent_output.get('evidence', []), ensure_ascii=False, indent=2)}

メリット:
{json.dumps(proponent_output.get('benefits', []), ensure_ascii=False, indent=2)}

確信度: {proponent_output.get('confidence', 0.0)}

=== 反対派（Opponent）の主張 ===

立場: {opponent_output.position}

反論:
{json.dumps(opponent_output.counter_arguments, ensure_ascii=False, indent=2)}

リスク:
{json.dumps(opponent_output.risks, ensure_ascii=False, indent=2)}

弱点:
{json.dumps(opponent_output.weaknesses, ensure_ascii=False, indent=2)}

代替案:
{json.dumps(opponent_output.alternatives, ensure_ascii=False, indent=2)}

確信度: {opponent_output.confidence}

双方を客観的に評価し、バランスの取れた最終判断を提示してください。"""

        adapter = get_adapter(provider)
        schema = MODERATOR_JSON_SCHEMA
        if provider == "gemini":
            schema = deepcopy(MODERATOR_JSON_SCHEMA)
            _apply_property_ordering(schema)

        response = await adapter.generate_structured(
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            system_prompt=MODERATOR_SYSTEM_PROMPT,
            user_prompt=moderator_prompt,
            temperature=self.config.temperature,
            schema=schema,
            schema_name="moderator_output",
            output_model=ModeratorOutput,
        )

        raw = StageRawData(
            provider=provider,
            model=self.config.model,
            system_prompt=MODERATOR_SYSTEM_PROMPT,
            user_prompt=moderator_prompt,
            request=response.request,
            response_text=response.response_text,
            response_meta=response.response_meta,
        )

        parsed_output = response.parsed_output
        if parsed_output is not None:
            if not isinstance(parsed_output, ModeratorOutput):
                raise ValueError("Anthropic structured output missing for ModeratorOutput")
            parsed = parsed_output
        else:
            parsed = self._parse_response(response.response_text)

        raw.parsed_output = parsed.model_dump()
        return parsed, raw

    def _parse_response(self, text: str) -> ModeratorOutput:
        cleaned = _strip_code_fences(text)
        try:
            return ModeratorOutput.model_validate_json(cleaned)
        except Exception as exc:
            raise ValueError("Moderator構造化出力の解析に失敗しました") from exc
