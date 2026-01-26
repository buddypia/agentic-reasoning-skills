"""Anthropic用ユーティリティ。

Anthropic Messages API は `max_tokens` が必須です。一方で、本サンプルでは特に出力トークン数を
制限したい要件がないため、固定値（ハードコード）で上限を設けないようにします。

実装方針:
  - Anthropic公式ドキュメントの「Max output」(最大出力トークン) を `max_tokens` に設定
  - 非ストリーミング利用のため、SDKが定義する上限（または安全なデフォルト）でキャップする
  - 未知のモデルは、エラーメッセージから許容上限らしき数値を抽出して再試行
  - 成功した値をモデルID単位でキャッシュし、次回以降の余計なリトライを避ける
"""

from __future__ import annotations

import re
from typing import Any, Awaitable, Callable

_MAX_TOKENS_BY_MODEL: dict[str, int] = {}
_NONSTREAMING_MAX_TOKENS_DEFAULT = 8192

# Anthropic docs のモデル比較表（Max output）を参照して設定。
# https://docs.anthropic.com/en/docs/about-claude/models/all-models
#
# ※ -latest / -0 / -1 などのエイリアスも同表の "Model aliases" に従い同値にしています。
_DOC_MAX_OUTPUT_TOKENS: dict[str, int] = {
    # Claude Sonnet 4
    "claude-sonnet-4-20250514": 64000,
    "claude-sonnet-4-0": 64000,
    # Claude Opus 4 / 4.1
    "claude-opus-4-20250514": 32000,
    "claude-opus-4-0": 32000,
    "claude-opus-4-1-20250805": 32000,
    "claude-opus-4-1": 32000,
    # Claude Sonnet 3.7
    "claude-3-7-sonnet-20250219": 64000,
    "claude-3-7-sonnet-latest": 64000,
    # Claude Sonnet 3.5
    "claude-3-5-sonnet-20241022": 8192,
    "claude-3-5-sonnet-latest": 8192,
    # Claude Haiku 3.5
    "claude-3-5-haiku-20241022": 8192,
    "claude-3-5-haiku-latest": 8192,
    # Claude Haiku 3
    "claude-3-haiku-20240307": 4096,
}


def _canonicalize_model(model: str) -> str:
    # 互換性のため、モデル文字列に付与されることがあるサフィックス（例: ":high"）を除去。
    return model.split(":", 1)[0].strip()


def _get_nonstreaming_max_tokens(model: str) -> int:
    """Non-streaming上限を取得。未定義の場合は安全なデフォルトを返す。"""
    try:
        from anthropic._constants import MODEL_NONSTREAMING_TOKENS
    except Exception:
        return _NONSTREAMING_MAX_TOKENS_DEFAULT
    return MODEL_NONSTREAMING_TOKENS.get(model, _NONSTREAMING_MAX_TOKENS_DEFAULT)


def get_anthropic_max_tokens(model: str) -> int | None:
    """モデルの最大出力トークン（Max output）を返す。未知なら None。"""
    key = _canonicalize_model(model)
    return _DOC_MAX_OUTPUT_TOKENS.get(key)


def _infer_allowed_max_tokens(message: str, requested: int) -> int | None:
    lowered = message.lower()
    if "max_tokens" not in lowered:
        return None

    numbers = [int(x) for x in re.findall(r"\d+", message)]
    candidates = [n for n in numbers if 0 < n < requested]
    if not candidates:
        return None
    return max(candidates)


async def create_message_with_auto_max_tokens(
    create_fn: Callable[..., Awaitable[Any]],
    *,
    model: str,
    max_attempts: int = 3,
    **kwargs: Any,
) -> tuple[Any, int]:
    """`max_tokens` の上限をハードコードせずに Anthropic の create を呼び出す。

    返り値:
        (response, used_max_tokens)
    """
    canonical_model = _canonicalize_model(model)
    nonstreaming_cap = _get_nonstreaming_max_tokens(canonical_model)
    doc_max = get_anthropic_max_tokens(canonical_model)
    max_tokens = _MAX_TOKENS_BY_MODEL.get(canonical_model, doc_max)
    if max_tokens is None:
        max_tokens = nonstreaming_cap
    if max_tokens > nonstreaming_cap:
        max_tokens = nonstreaming_cap
    last_exc: Exception | None = None

    for _ in range(max_attempts):
        try:
            response = await create_fn(model=model, max_tokens=max_tokens, **kwargs)
            _MAX_TOKENS_BY_MODEL[canonical_model] = max_tokens
            return response, max_tokens
        except Exception as exc:  # noqa: BLE001 - SDK例外が複数あるためまとめて扱う
            last_exc = exc
            inferred = _infer_allowed_max_tokens(str(exc), max_tokens)
            if inferred is None or inferred >= max_tokens:
                raise
            max_tokens = inferred
            _MAX_TOKENS_BY_MODEL[canonical_model] = max_tokens

    assert last_exc is not None
    raise last_exc
