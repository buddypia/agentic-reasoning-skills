"""Provider adapters — 구독 인증 CLI 백엔드(순수 CLI).

별도 API 키 없이 사용자의 구독 인증으로 최신 모델을 호출한다:
  - gemini             → Antigravity CLI (`agy -p`)    : 평문 출력 → JSON-only 지시 + Pydantic 검증
  - anthropic / claude → Claude Code     (`claude -p`) : --json-schema 네이티브 구조화 출력
  - openai             → Codex           (`codex exec`): --output-schema 네이티브 구조화 출력

장문(long-form) 입력은 전부 stdin 경유(ARG_MAX / shell escaping 회피).
역할 executor 는 무수정 — generate_structured() 인터페이스로 ProviderResponse 만 반환.

환경 변수:
  MULTILLM_REASONING_EFFORT   추론 강도 (기본 xhigh; Codex 에 적용)
  MULTILLM_CLI_TIMEOUT        CLI 호출 타임아웃(초) (기본 360)
  MULTILLM_AGY_PRINT_TIMEOUT  agy --print-timeout 값 (기본 5m)
  MULTILLM_CLAUDE_MODEL / MULTILLM_CODEX_MODEL  per-backend 모델 override (옵션)
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any, Protocol

from .raw import to_jsonable


# =============================================================================
# CLI 공통 헬퍼
# =============================================================================

def _cli_timeout() -> float:
    try:
        return float(os.getenv("MULTILLM_CLI_TIMEOUT", "360"))
    except ValueError:
        return 360.0


def _reasoning_effort() -> str:
    return os.getenv("MULTILLM_REASONING_EFFORT", "xhigh").strip() or "xhigh"


def _agy_print_timeout() -> str:
    return os.getenv("MULTILLM_AGY_PRINT_TIMEOUT", "5m").strip() or "5m"


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    cleaned = cleaned.strip("`").strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    return cleaned


async def _run_cli(
    cmd: list[str],
    *,
    stdin_text: str | None,
    cwd: str | None,
    timeout: float,
) -> tuple[int, str, str]:
    """CLI 를 subprocess 로 실행. 장문 입력은 stdin 경유. (rc, stdout, stderr) 반환."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if stdin_text is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    payload = stdin_text.encode("utf-8") if stdin_text is not None else None
    try:
        out, err = await asyncio.wait_for(proc.communicate(payload), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        raise RuntimeError(f"CLI timeout after {timeout}s: {cmd[0]}")
    rc = proc.returncode if proc.returncode is not None else 0
    return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


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


# =============================================================================
# Claude Code CLI  (anthropic / claude)  — claude -p --json-schema (네이티브 구조화)
# =============================================================================

class ClaudeCliAdapter:
    name = "claude"

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
        binary = shutil.which("claude") or "claude"
        model_id = os.getenv("MULTILLM_CLAUDE_MODEL") or model
        timeout = _cli_timeout()
        with tempfile.TemporaryDirectory(prefix="mll_claude_") as tmp:
            sys_file = os.path.join(tmp, "system.txt")
            with open(sys_file, "w", encoding="utf-8") as fh:
                fh.write(system_prompt)
            cmd = [
                binary, "-p",
                "--output-format", "json",
                "--json-schema", json.dumps(schema, ensure_ascii=False),
                "--append-system-prompt-file", sys_file,
                "--allowed-tools", "",
                "--permission-mode", "dontAsk",
                "--model", model_id,
            ]
            # cwd=tmp → 프로젝트 CLAUDE.md/hooks 로드 회피. 구독 인증 위해 --bare 미사용.
            rc, out, err = await _run_cli(cmd, stdin_text=user_prompt, cwd=tmp, timeout=timeout)
        if rc != 0:
            raise RuntimeError(f"claude -p 실패 (exit {rc}): {err.strip()[:500]}")
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"claude -p JSON 봉투 파싱 실패: {out[:300]}") from exc
        if data.get("is_error"):
            raise RuntimeError(f"claude -p error: {str(data.get('result', ''))[:300]}")
        structured = data.get("structured_output")
        if structured is not None:
            response_text = json.dumps(structured, ensure_ascii=False)
        else:
            response_text = data.get("result", "") or ""
        request = {
            "backend": "claude-cli",
            "model": model_id,
            "argv": cmd,
            "system_prompt_chars": len(system_prompt),
            "user_prompt_chars": len(user_prompt),
        }
        meta = {
            "backend": "claude-cli",
            "model": model_id,
            "usage": data.get("modelUsage") or data.get("usage"),
            "session_id": data.get("session_id"),
        }
        return ProviderResponse(
            provider=self.name,
            model=model_id,
            request=to_jsonable(request),
            response_text=response_text,
            response_meta=meta,
        )


# =============================================================================
# Codex CLI  (openai)  — codex exec --output-schema (네이티브 구조화), reasoning xhigh
# =============================================================================

class CodexAdapter:
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
        binary = shutil.which("codex") or "codex"
        model_id = os.getenv("MULTILLM_CODEX_MODEL") or model
        effort = _reasoning_effort()
        timeout = _cli_timeout()
        with tempfile.TemporaryDirectory(prefix="mll_codex_") as tmp:
            schema_file = os.path.join(tmp, "schema.json")
            out_file = os.path.join(tmp, "out.json")
            with open(schema_file, "w", encoding="utf-8") as fh:
                json.dump(schema, fh, ensure_ascii=False)
            cmd = [
                binary, "exec",
                system_prompt,                      # 역할 지시문 = prompt arg
                "--output-schema", schema_file,
                "-o", out_file,
                "-m", model_id,
                "-c", f"model_reasoning_effort={effort}",
                "-s", "read-only",
                "--skip-git-repo-check",
                "--ephemeral",
            ]
            # 장문 컨텍스트(user_prompt) → stdin (codex 가 <stdin> 블록으로 append)
            rc, out, err = await _run_cli(cmd, stdin_text=user_prompt, cwd=tmp, timeout=timeout)
            response_text = ""
            try:
                with open(out_file, "r", encoding="utf-8") as fh:
                    response_text = fh.read().strip()
            except FileNotFoundError:
                response_text = ""
        if not response_text:
            if rc != 0:
                raise RuntimeError(f"codex exec 실패 (exit {rc}): {err.strip()[:500]}")
            raise RuntimeError(f"codex exec 구조화 출력 없음: {err.strip()[:300]}")
        request = {
            "backend": "codex-cli",
            "model": model_id,
            "reasoning_effort": effort,
            "argv": cmd,
            "system_prompt_chars": len(system_prompt),
            "user_prompt_chars": len(user_prompt),
        }
        meta = {"backend": "codex-cli", "model": model_id, "reasoning_effort": effort}
        return ProviderResponse(
            provider=self.name,
            model=model_id,
            request=to_jsonable(request),
            response_text=response_text,
            response_meta=meta,
        )


# =============================================================================
# Antigravity CLI  (gemini)  — Gemini CLI 후속. 기본 모델 Gemini 3.5 Flash (High).
#   agy 0.42.0 는 --output-format/--model/reasoning 플래그 미지원 → 평문 출력을
#   JSON-only 지시로 유도하고 executor 의 Pydantic 검증 경로로 파싱한다.
# =============================================================================

class AntigravityCliAdapter:
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
        binary = shutil.which("agy") or "agy"
        timeout = _cli_timeout()
        directive = (
            f"{system_prompt}\n\n"
            "[중요] 아래 stdin 본문을 토대로, 코드펜스나 부가 설명 없이 "
            "다음 JSON 스키마에 정확히 부합하는 JSON 객체 하나만 출력하세요:\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        cmd = [
            binary, "-p", directive,
            "--dangerously-skip-permissions",
            "--print-timeout", _agy_print_timeout(),
        ]
        # agy 는 cwd 에 .antigravitycli/ 作業ディレクトリを生成するため tempdir で隔離する。
        tmp = tempfile.mkdtemp(prefix="mll_agy_")
        last_err = ""
        try:
            for attempt in range(2):
                rc, out, err = await _run_cli(cmd, stdin_text=user_prompt, cwd=tmp, timeout=timeout)
                text = _strip_code_fences(out.strip())
                if rc == 0 and text:
                    request = {
                        "backend": "antigravity-cli",
                        "model": model,
                        "directive_chars": len(directive),
                        "user_prompt_chars": len(user_prompt),
                        "attempt": attempt + 1,
                    }
                    meta = {"backend": "antigravity-cli", "model": model, "attempt": attempt + 1}
                    return ProviderResponse(
                        provider=self.name,
                        model=model,
                        request=to_jsonable(request),
                        response_text=text,
                        response_meta=meta,
                    )
                last_err = err.strip()[:300] or f"exit {rc}"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"agy -p 실패: {last_err}")


# =============================================================================
# Mock  (offline smoke tests)
# =============================================================================

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
    if schema_name == "decomposition_output":
        return {
            "subtasks": ["mock-subtask"],
            "assumptions": ["mock-assumption"],
            "constraints": ["mock-constraint"],
            "questions": ["mock-question"],
            "confidence": 0.5,
        }
    if schema_name == "solution_output":
        return {
            "solutions": [{"subtask": "mock-subtask", "answer": "mock-answer"}],
            "open_questions": ["mock-open-question"],
            "risks": ["mock-risk"],
            "confidence": 0.5,
        }
    if schema_name == "verification_output":
        return {
            "issues": ["mock-issue"],
            "corrections": ["mock-correction"],
            "self_corrections": ["mock-self-correction"],
            "validation_notes": ["mock-note"],
            "confidence": 0.5,
        }
    if schema_name == "integration_output":
        return {
            "integrated_answer": "mock-integrated-answer",
            "applied_corrections": ["mock-applied"],
            "confidence": 0.5,
        }
    if schema_name == "reflection_output":
        return {
            "final_response": "mock-final-response",
            "confidence_score": 0.5,
            "uncertainties": ["mock-uncertainty"],
            "self_corrections": ["mock-self-correction"],
            "reflection_notes": ["mock-note"],
        }
    return {"message": f"mock-response for {schema_name}", "prompt": user_prompt}


def get_adapter(provider: str) -> ProviderAdapter:
    normalized = provider.strip().lower()
    if normalized == "mock":
        return MockAdapter()
    if normalized == "openai":
        return CodexAdapter()
    if normalized in {"anthropic", "claude"}:
        return ClaudeCliAdapter()
    if normalized == "gemini":
        return AntigravityCliAdapter()
    raise ValueError(f"Unknown provider: {provider}")
