#!/usr/bin/env python3
"""
マルチLLM リフレクションパターン ワークフロー

複数のLLMを使用したリフレクション（レビュー＆改善）パターンを実装:
- Generator (Gemini): 初期ドラフトを作成
- Critic (Claude): レビューとフィードバックを提供
- Refiner (OpenAI): 洗練された最終版を作成

使用方法:
    # CLIモード
    python main.py "AI技術トレンドを整理して要約してください"

    # DevUIモード（現在は非対応）
    python main.py --devui --port 8095

    # 設定ファイルを使用（config.yaml を自動探索。明示指定も可能）
    python main.py --config config.yaml "プロンプト"  # 明示指定

    # カスタムモデル指定
    python main.py "Your prompt" \\
        --generator-model gemini-3-pro-preview \\
        --critic-model claude-opus-4-1-20250805 \\
        --refiner-model gpt-5.2

設定の優先順位:
    CLI引数 > 環境変数 > 設定ファイル > デフォルト値
"""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    print(
        "依存関係が不足しています: python-dotenv\n"
        "対処: scripts/requirements.txt をインストールしてください。\n"
        "例: python3.13 -m venv .venv && source .venv/bin/activate && "
        "pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import yaml
except ImportError:  # pragma: no cover
    print(
        "依存関係が不足しています: pyyaml\n"
        "対処: scripts/requirements.txt をインストールしてください。\n"
        "例: python3.13 -m venv .venv && source .venv/bin/activate && "
        "pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

from workflow.engine import WorkflowRunResult

from workflow.config import AgentConfig
from workflow.settings import (
    AVAILABLE_PROVIDERS,
    DEFAULT_MODELS,
    GENERATOR_DEFAULTS,
    CRITIC_DEFAULTS,
    REFINER_DEFAULTS,
    get_random_providers,
    get_shuffled_providers,
    GENERATOR_ENV_KEYS,
    CRITIC_ENV_KEYS,
    REFINER_ENV_KEYS,
    print_config_info,
    resolve_provider_with_random,
)
from workflow.workflow import build_reflection_workflow
from workflow.types import ReflectionResult


DEFAULT_DEVUI_PORT = 8095
DEFAULT_CONFIG_PATHS = [
    "config.yaml",
    "config.yml",
    "config.json",
    ".config.yaml",
    ".config.yml",
    ".config.json",
]


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower()


def _resolve_provider_env_keys(provider: str) -> tuple[str, str]:
    normalized = _normalize_provider(provider)
    if normalized == "gemini":
        return "GEMINI_API_KEY", "GEMINI_MODEL_ID"
    if normalized in {"anthropic", "claude"}:
        return "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL_ID"
    if normalized == "openai":
        return "OPENAI_API_KEY", "OPENAI_CHAT_MODEL_ID"
    if normalized == "mock":
        return "", ""
    return "", ""


def _load_config_file(config_path: str) -> dict[str, Any]:
    if config_path.endswith((".yaml", ".yml")):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    if config_path.endswith(".json"):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise ValueError(f"サポートされていない設定ファイル形式です: {config_path}")


def _resolve_config_path(args: argparse.Namespace) -> Optional[str]:
    if getattr(args, "no_config", False):
        return None

    explicit = getattr(args, "config", None)
    if explicit:
        if not os.path.exists(explicit):
            print(f"エラー: 設定ファイルが見つかりません: {explicit}", file=sys.stderr)
            sys.exit(1)
        return explicit

    env_path = os.getenv("CONFIG_FILE")
    if env_path:
        if not os.path.exists(env_path):
            print(f"エラー: CONFIG_FILE で指定されたファイルが見つかりません: {env_path}", file=sys.stderr)
            sys.exit(1)
        return env_path

    for candidate in DEFAULT_CONFIG_PATHS:
        if os.path.exists(candidate):
            return candidate

    skill_root = Path(__file__).resolve().parents[1]
    for candidate in DEFAULT_CONFIG_PATHS:
        skill_candidate = skill_root / candidate
        if skill_candidate.exists():
            return str(skill_candidate)

    return None


def _coerce_float(value: object, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _coerce_int(value: object, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _is_truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _get_global_config(config: dict[str, Any]) -> dict[str, Any]:
    return _get_dict(config.get("global") or config.get("common") or {})


def _resolve_provider_strategy(
    *,
    args: argparse.Namespace,
    config_file: dict[str, Any],
) -> Optional[str]:
    if getattr(args, "random_providers", False):
        return "random"
    if getattr(args, "shuffle_providers", False):
        return "shuffle"

    env_strategy = os.getenv("REFLECTION_PROVIDER_STRATEGY") or os.getenv("REFLECTION_PROVIDER_MODE")
    if env_strategy:
        normalized = env_strategy.strip().lower()
        if normalized in {"random", "shuffle", "fixed"}:
            return normalized

    if _is_truthy(os.getenv("REFLECTION_RANDOM_PROVIDERS")):
        return "random"
    if _is_truthy(os.getenv("REFLECTION_SHUFFLE_PROVIDERS")):
        return "shuffle"

    global_cfg = _get_global_config(config_file)
    if "provider_strategy" in global_cfg:
        normalized = str(global_cfg.get("provider_strategy")).strip().lower()
        if normalized in {"random", "shuffle", "fixed"}:
            return normalized

    return None


def _resolve_temperature(
    *,
    args: argparse.Namespace,
    env_key_role: str,
    env_prefix: str,
    agent_cfg: dict[str, Any],
    global_cfg: dict[str, Any],
    default: float,
) -> float:
    if getattr(args, "temperature", None) is not None:
        return float(args.temperature)

    if os.getenv(env_key_role) is not None:
        return _coerce_float(os.getenv(env_key_role), default)

    env_global = os.getenv(f"{env_prefix}_TEMPERATURE") or os.getenv("LLM_TEMPERATURE")
    if env_global is not None:
        return _coerce_float(env_global, default)

    if "temperature" in agent_cfg:
        return _coerce_float(agent_cfg.get("temperature"), default)

    if "temperature" in global_cfg:
        return _coerce_float(global_cfg.get("temperature"), default)

    return default


def _resolve_agent_config(
    *,
    args: argparse.Namespace,
    config_file: dict[str, Any],
    name: str,
    role: str,
    env_keys,
    default_provider: str,
    default_temperature: float,
    force_random: bool = False,
) -> AgentConfig:
    global_cfg = _get_global_config(config_file)
    agent_cfg = _get_dict(config_file.get(role))

    # プロバイダーの取得（--random-providers または --<role>-provider random の場合はランダム選択）
    raw_provider = (
        getattr(args, f"{role}_provider", None)
        or os.getenv(env_keys.provider)
        or agent_cfg.get("provider")
    )

    if force_random and raw_provider is None:
        raw_provider = "random"

    provider = resolve_provider_with_random(
        provider=raw_provider,
        default_provider=default_provider,
        available_providers=AVAILABLE_PROVIDERS,
    )

    _, provider_model_env = _resolve_provider_env_keys(provider)

    model = (
        getattr(args, f"{role}_model", None)
        or os.getenv(env_keys.model)
        or (os.getenv(provider_model_env) if provider_model_env else None)
        or agent_cfg.get("model")
        or DEFAULT_MODELS.get(provider, "gpt-5.2")
    )

    cli_api_key = None
    if provider == "gemini":
        cli_api_key = getattr(args, "gemini_api_key", None)
    elif provider in {"anthropic", "claude"}:
        cli_api_key = getattr(args, "anthropic_api_key", None)
    elif provider == "openai":
        cli_api_key = getattr(args, "openai_api_key", None)

    provider_api_key_env, _ = _resolve_provider_env_keys(provider)
    api_key = (
        cli_api_key
        or os.getenv(env_keys.api_key)
        or (os.getenv(provider_api_key_env) if provider_api_key_env else None)
        or agent_cfg.get("api_key")
    )

    base_url = None
    if provider == "openai":
        base_url = (
            getattr(args, "openai_base_url", None)
            or os.getenv(env_keys.base_url)
            or os.getenv("OPENAI_BASE_URL")
            or agent_cfg.get("base_url")
        )
    else:
        base_url = os.getenv(env_keys.base_url) or agent_cfg.get("base_url")

    temperature = _resolve_temperature(
        args=args,
        env_key_role=env_keys.temperature,
        env_prefix="REFLECTION",
        agent_cfg=agent_cfg,
        global_cfg=global_cfg,
        default=default_temperature,
    )

    return AgentConfig(
        name=name,
        role=role,
        provider=provider,
        model=str(model),
        api_key=str(api_key) if api_key is not None else None,
        base_url=str(base_url) if base_url is not None else None,
        temperature=temperature,
    )


def _resolve_devui_port(args: argparse.Namespace, config_file: dict[str, Any]) -> int:
    if getattr(args, "port", None) is not None:
        return int(args.port)

    env_port = os.getenv("REFLECTION_DEVUI_PORT") or os.getenv("DEVUI_PORT")
    if env_port is not None:
        return _coerce_int(env_port, DEFAULT_DEVUI_PORT)

    devui_cfg = _get_dict(config_file.get("devui"))
    if "port" in devui_cfg:
        return _coerce_int(devui_cfg.get("port"), DEFAULT_DEVUI_PORT)

    return DEFAULT_DEVUI_PORT


def _require_api_key(config: AgentConfig) -> None:
    provider = _normalize_provider(config.provider)
    if provider == "mock":
        return
    if config.api_key:
        return
    provider_env, _ = _resolve_provider_env_keys(config.provider)
    cli_flag = {
        "gemini": "--gemini-api-key",
        "anthropic": "--anthropic-api-key",
        "claude": "--anthropic-api-key",
        "openai": "--openai-api-key",
    }.get(provider, None)
    print(f"エラー: {config.name} のAPIキーが見つかりません（provider={provider}）。", file=sys.stderr)
    if provider_env:
        print(f"  環境変数: {config.role.upper()}固有（例: REFLECTION_{config.role.upper()}_API_KEY） または {provider_env}", file=sys.stderr)
    if cli_flag:
        print(f"  CLI: {cli_flag}", file=sys.stderr)
    sys.exit(1)


@dataclass(frozen=True)
class RuntimeConfig:
    config_path: Optional[str]
    devui_port: int
    generator: AgentConfig
    critic: AgentConfig
    refiner: AgentConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="リフレクションパターン マルチLLM ワークフロー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
使用例:
    python main.py "AIに関するブログ記事を書いて"
    python main.py --devui --port 8095
    python main.py --config config.yaml "プロンプト"
    python main.py "REST API設計を作成して" --temperature 0.5

デフォルト値:
    Generator: {GENERATOR_DEFAULTS.provider}/{GENERATOR_DEFAULTS.get_model()}
    Critic: {CRITIC_DEFAULTS.provider}/{CRITIC_DEFAULTS.get_model()}
    Refiner: {REFINER_DEFAULTS.provider}/{REFINER_DEFAULTS.get_model()}

設定の優先順位: CLI引数 > 環境変数 > 設定ファイル > デフォルト値
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="リフレクションワークフローで処理するプロンプト",
    )

    # 設定ファイルオプション
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="設定ファイルのパス (YAML/JSON)。未指定の場合は config.yaml/config.json を自動探索",
    )
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="設定ファイルの自動読み込みを無効化",
    )

    # DevUIオプション
    parser.add_argument(
        "--devui",
        action="store_true",
        help="インタラクティブなWeb UIのDevUIモードで実行（現在は非対応）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"DevUIサーバーのポート番号 (デフォルト: {DEFAULT_DEVUI_PORT})",
    )

    # ランダムプロバイダー選択オプション
    parser.add_argument(
        "--random-providers",
        action="store_true",
        help="全エージェントのプロバイダーをランダムに選択（gemini/anthropic/openaiからランダム）",
    )
    parser.add_argument(
        "--shuffle-providers",
        action="store_true",
        help="全エージェントのプロバイダーをシャッフルして割り当て（重複なし）",
    )

    # Generator (Gemini) オプション
    parser.add_argument(
        "--generator-provider",
        default=None,
        help=f"Generatorエージェントのプロバイダ (デフォルト: {GENERATOR_DEFAULTS.provider})。'random'を指定するとランダム選択",
    )
    parser.add_argument(
        "--generator-model",
        default=None,
        help=f"GeneratorのモデルID (デフォルト: {GENERATOR_DEFAULTS.get_model()})",
    )
    parser.add_argument(
        "--gemini-api-key",
        default=None,
        help="Gemini APIキー (または GEMINI_API_KEY 環境変数を設定)",
    )

    # Critic (Claude) オプション
    parser.add_argument(
        "--critic-provider",
        default=None,
        help=f"Criticエージェントのプロバイダ (デフォルト: {CRITIC_DEFAULTS.provider})。'random'を指定するとランダム選択",
    )
    parser.add_argument(
        "--critic-model",
        default=None,
        help=f"CriticのモデルID (デフォルト: {CRITIC_DEFAULTS.get_model()})",
    )
    parser.add_argument(
        "--anthropic-api-key",
        default=None,
        help="Anthropic APIキー (または ANTHROPIC_API_KEY 環境変数を設定)",
    )

    # Refiner (OpenAI) オプション
    parser.add_argument(
        "--refiner-provider",
        default=None,
        help=f"Refinerエージェントのプロバイダ (デフォルト: {REFINER_DEFAULTS.provider})。'random'を指定するとランダム選択",
    )
    parser.add_argument(
        "--refiner-model",
        default=None,
        help=f"RefinerのモデルID (デフォルト: {REFINER_DEFAULTS.get_model()})",
    )
    parser.add_argument(
        "--openai-api-key",
        default=None,
        help="OpenAI APIキー (または OPENAI_API_KEY 環境変数を設定)",
    )
    parser.add_argument(
        "--openai-base-url",
        default=None,
        help="OpenAI ベースURL (オプション)",
    )

    # 共通オプション
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help=f"全エージェントのtemperature (デフォルト: {GENERATOR_DEFAULTS.temperature})",
    )
    # 出力オプション
    parser.add_argument(
        "--json",
        action="store_true",
        help="結果をJSON形式で出力",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細出力を表示（デフォルトは最終コンテンツのみ）",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="サニタイズされたLLMリクエスト/レスポンスの生データを含める (デバッグ用。テキスト出力では --verbose 時のみ表示)",
    )
    parser.add_argument(
        "--raw-output",
        default=None,
        help="サニタイズされたLLM生データをJSONファイルに書き込む",
    )
    parser.add_argument(
        "--raw-max-chars",
        type=int,
        default=8000,
        help="表示時の生テキストフィールドあたりの最大文字数 (デフォルト: 8000)。0で無制限。",
    )

    # デバッグオプション
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="解決済みの設定を表示して終了 (デバッグ用)",
    )

    return parser.parse_args()


def get_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    """CLI引数、環境変数、設定ファイルから実行時設定を解決する。"""

    config_path = _resolve_config_path(args)
    config_file: dict[str, Any] = {}
    if config_path:
        try:
            config_file = _load_config_file(config_path)
        except Exception as exc:
            print(f"エラー: 設定ファイルの読み込みに失敗しました: {config_path}\n  {exc}", file=sys.stderr)
            sys.exit(1)

    provider_strategy = _resolve_provider_strategy(args=args, config_file=config_file)
    generator_default_provider = GENERATOR_DEFAULTS.provider
    critic_default_provider = CRITIC_DEFAULTS.provider
    refiner_default_provider = REFINER_DEFAULTS.provider
    if provider_strategy == "random":
        (
            generator_default_provider,
            critic_default_provider,
            refiner_default_provider,
        ) = get_random_providers()
    elif provider_strategy == "shuffle":
        (
            generator_default_provider,
            critic_default_provider,
            refiner_default_provider,
        ) = get_shuffled_providers()

    force_random = getattr(args, "random_providers", False)

    generator = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Generator",
        role="generator",
        env_keys=GENERATOR_ENV_KEYS,
        default_provider=generator_default_provider,
        default_temperature=GENERATOR_DEFAULTS.temperature,
        force_random=force_random,
    )
    critic = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Critic",
        role="critic",
        env_keys=CRITIC_ENV_KEYS,
        default_provider=critic_default_provider,
        default_temperature=CRITIC_DEFAULTS.temperature,
        force_random=force_random,
    )
    refiner = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Refiner",
        role="refiner",
        env_keys=REFINER_ENV_KEYS,
        default_provider=refiner_default_provider,
        default_temperature=REFINER_DEFAULTS.temperature,
        force_random=force_random,
    )

    devui_port = _resolve_devui_port(args, config_file)

    return RuntimeConfig(
        config_path=config_path,
        devui_port=devui_port,
        generator=generator,
        critic=critic,
        refiner=refiner,
    )


def print_config_summary(runtime: RuntimeConfig) -> None:
    """解決済みの設定サマリーを出力する（APIキーは表示しない）。"""
    print("\n=== 設定サマリー ===")
    print(f"設定ファイル: {runtime.config_path or '(なし)'}")
    print(f"DevUI Port: {runtime.devui_port}")
    print(f"Generator: {runtime.generator.provider}/{runtime.generator.model} (temp={runtime.generator.temperature})")
    print(f"Critic:    {runtime.critic.provider}/{runtime.critic.model} (temp={runtime.critic.temperature})")
    print(f"Refiner:   {runtime.refiner.provider}/{runtime.refiner.model} (temp={runtime.refiner.temperature})")
    print("===================\n")


def _truncate_strings(value: object, max_chars: int) -> object:
    if max_chars <= 0:
        return value
    if isinstance(value, str):
        if len(value) <= max_chars:
            return value
        return value[:max_chars] + "\n...<truncated>"
    if isinstance(value, list):
        return [_truncate_strings(v, max_chars) for v in value]
    if isinstance(value, dict):
        return {k: _truncate_strings(v, max_chars) for k, v in value.items()}
    return value


def print_result(
    result: ReflectionResult,
    verbose: bool = False,
    as_json: bool = False,
    include_raw: bool = False,
    raw_max_chars: int = 8000,
) -> None:
    """リフレクション結果を読みやすい形式で出力する。"""

    if as_json:
        if include_raw:
            print(result.model_dump_json(indent=2, ensure_ascii=False, exclude_none=True))
        else:
            print(result.model_dump_json(indent=2, ensure_ascii=False, exclude_none=True, exclude={"raw"}))
        return

    # デフォルト（オプションなし）: 最終結果のみを出力
    if not verbose:
        print(result.final_content)
        return

    print("\n" + "=" * 70)
    print("リフレクション ワークフロー 結果")
    print("=" * 70)

    print("\n--- 元のプロンプト ---")
    print(result.original_prompt)

    print("\n--- ステージ1: 初期ドラフト (Generator) ---")
    print(f"モデル: {result.generator_model}")
    print(f"確信度: {result.generator_confidence:.2f}")
    print("-" * 40)
    print(result.initial_draft)

    print("\n--- ステージ2: 批評 (Critic) ---")
    print(f"モデル: {result.critic_model}")
    print(f"スコア: {result.critic_score}/10")
    print("\n強み:")
    for s in result.critic_strengths:
        print(f"  + {s}")
    print("\n弱み:")
    for w in result.critic_weaknesses:
        print(f"  - {w}")
    print("\n改善提案:")
    for s in result.critic_suggestions:
        print(f"  > {s}")

    print("\n--- ステージ3: 改善版 (Refiner) ---")
    print(f"モデル: {result.refiner_model}")
    print(f"最終スコア: {result.final_score}/10")
    print("\n実施した改善:")
    for imp in result.improvements_made:
        print(f"  * {imp}")
    print("-" * 40)

    print("\n### 最終コンテンツ ###\n")
    print(result.final_content)

    print("\n" + "-" * 70)
    print(f"総処理時間: {result.total_duration_sec:.2f}秒")
    print(f"品質改善: {result.critic_score}/10 → {result.final_score}/10")
    print("=" * 70)

    if include_raw:
        print("\n--- RAWデータ (サニタイズ済み) ---")
        raw_data = result.raw.model_dump() if result.raw is not None else {}
        raw_data_view = _truncate_strings(raw_data, raw_max_chars)
        print(json.dumps(raw_data_view, ensure_ascii=False, indent=2))


def _extract_reflection_result(run_result: object) -> ReflectionResult | None:
    """workflow.run()の異なる戻り値の型から最終的なReflectionResultを抽出する。

    WorkflowRunResult（イベント）を返す場合や、モデルを直接返す場合に備えて
    互換性を維持するためのヘルパー。
    """

    if isinstance(run_result, ReflectionResult):
        return run_result

    outputs: list[object] = []

    if WorkflowRunResult is not None and isinstance(run_result, WorkflowRunResult):
        outputs = run_result.get_outputs()
    elif isinstance(run_result, list):
        # 後方互換性: 単純なリストをイベントリストとして扱い、`.data`を抽出する。
        for event in run_result:
            data = getattr(event, "data", None)
            if data is not None:
                outputs.append(data)

    for candidate in reversed(outputs):
        if isinstance(candidate, ReflectionResult):
            return candidate
        try:
            return ReflectionResult.model_validate(candidate)
        except Exception:
            continue

    return None


async def run_cli(args: argparse.Namespace, runtime: RuntimeConfig) -> None:
    """CLIモードでワークフローを実行する。"""

    if not args.prompt:
        print("エラー: CLIモードではプロンプトが必要です")
        print("使用方法: python main.py 'ここにプロンプトを入力'")
        sys.exit(1)

    _require_api_key(runtime.generator)
    _require_api_key(runtime.critic)
    _require_api_key(runtime.refiner)

    generator_config = runtime.generator
    critic_config = runtime.critic
    refiner_config = runtime.refiner

    log_stream = sys.stderr if args.json else sys.stdout
    if args.verbose:
        print(f"\nリフレクションワークフローを開始しています...", file=log_stream)
        print(f"  Generator: {generator_config.provider}/{generator_config.model}", file=log_stream)
        print(f"  Critic: {critic_config.provider}/{critic_config.model}", file=log_stream)
        print(f"  Refiner: {refiner_config.provider}/{refiner_config.model}", file=log_stream)
        print(file=log_stream)

    workflow = build_reflection_workflow(
        generator_config=generator_config,
        critic_config=critic_config,
        refiner_config=refiner_config,
    )

    run_result = await workflow.run(args.prompt)
    reflection_result = _extract_reflection_result(run_result)

    if reflection_result is None:
        print(f"エラー: ReflectionResultを抽出できませんでした: {type(run_result)}", file=sys.stderr)
        print(run_result)
        sys.exit(1)

    if args.raw_output:
        raw_data = reflection_result.raw.model_dump() if reflection_result.raw is not None else {}
        with open(args.raw_output, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        if args.verbose:
            print(f"生データを書き込みました: {args.raw_output}", file=sys.stderr if args.json else sys.stdout)

    print_result(
        reflection_result,
        verbose=args.verbose,
        as_json=args.json,
        include_raw=args.raw,
        raw_max_chars=args.raw_max_chars,
    )


def run_devui(args: argparse.Namespace, runtime: RuntimeConfig) -> None:
    """DevUIモードでワークフローを実行する。"""
    print("エラー: DevUIは軽量エンジンではサポートされていません。CLIをご利用ください。")
    sys.exit(1)


def main() -> None:
    load_dotenv()
    args = parse_args()

    # 設定を解決
    runtime = get_runtime_config(args)

    # --show-configが指定された場合は設定を表示して終了
    if getattr(args, "show_config", False):
        print_config_summary(runtime)
        print_config_info()
        sys.exit(0)

    if args.devui:
        run_devui(args, runtime)
    else:
        asyncio.run(run_cli(args, runtime))


if __name__ == "__main__":
    main()
