#!/usr/bin/env python3
"""
マルチLLM メタ認知パターン ワークフロー（5段階）

複数のLLMを使用したメタ認知（分解→解決→検証→統合→反省）:
- Decomposer: 課題の分解
- Solver: 解決案の作成
- Verifier: 検証と自己修正
- Integrator: 統合された回答草案
- Reflector: 反省・確信度付き最終回答

使用方法:
    # CLIモード
    python main.py "AI技術トレンドを整理して要約してください"

    # DevUIモード（現在は非対応）
    python main.py --devui --port 8095

    # 設定ファイルを使用（config.yaml を自動探索。明示指定も可能）
    python main.py --config config.yaml "プロンプト"  # 明示指定

    # カスタムモデル指定
    python main.py "Your prompt" \
        --decomposer-model gemini-3-pro-preview \
        --solver-model gemini-3-pro-preview \
        --verifier-model claude-opus-4-1-20250805 \
        --integrator-model gpt-5.2 \
        --reflector-model gpt-5.2

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
    DEFAULT_MODELS,
    get_random_providers,
    get_shuffled_providers,
    DECOMPOSER_DEFAULTS,
    SOLVER_DEFAULTS,
    VERIFIER_DEFAULTS,
    INTEGRATOR_DEFAULTS,
    REFLECTOR_DEFAULTS,
    DECOMPOSER_ENV_KEYS,
    SOLVER_ENV_KEYS,
    VERIFIER_ENV_KEYS,
    INTEGRATOR_ENV_KEYS,
    REFLECTOR_ENV_KEYS,
    print_config_info,
)
from workflow.workflow import build_metacognition_workflow
from workflow.types import MetaCognitionResult


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


def _get_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _get_global_config(config: dict[str, Any]) -> dict[str, Any]:
    return _get_dict(config.get("global") or config.get("common") or {})


def _is_truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_timeout_value(config: dict[str, Any]) -> object:
    if "timeout" in config:
        return config.get("timeout")
    return config.get("timeout_sec")


def _normalize_output_schema(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"nested", "full", "default"}:
        return "nested"
    if normalized in {"flat", "flattened"}:
        return "flat"
    return "nested"


def _resolve_output_schema(
    *,
    args: argparse.Namespace,
    config_file: dict[str, Any],
) -> str:
    if getattr(args, "output_schema", None):
        return _normalize_output_schema(str(args.output_schema))

    env_schema = os.getenv("METACOGNITION_OUTPUT_SCHEMA") or os.getenv("METACOGNITION_OUTPUT_FORMAT")
    if env_schema:
        return _normalize_output_schema(env_schema)

    global_cfg = _get_global_config(config_file)
    if "output_schema" in global_cfg:
        return _normalize_output_schema(str(global_cfg.get("output_schema")))

    return "nested"


def _resolve_provider_strategy(
    *,
    args: argparse.Namespace,
    config_file: dict[str, Any],
) -> Optional[str]:
    if getattr(args, "random_providers", False):
        return "random"
    if getattr(args, "shuffle_providers", False):
        return "shuffle"

    env_strategy = os.getenv("METACOGNITION_PROVIDER_STRATEGY") or os.getenv("METACOGNITION_PROVIDER_MODE")
    if env_strategy:
        normalized = env_strategy.strip().lower()
        if normalized in {"random", "shuffle", "fixed"}:
            return normalized

    if _is_truthy(os.getenv("METACOGNITION_RANDOM_PROVIDERS")):
        return "random"
    if _is_truthy(os.getenv("METACOGNITION_SHUFFLE_PROVIDERS")):
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


def _resolve_timeout(
    *,
    args: argparse.Namespace,
    env_key_role: str,
    env_prefix: str,
    agent_cfg: dict[str, Any],
    global_cfg: dict[str, Any],
    default: float,
) -> float:
    if getattr(args, "timeout", None) is not None:
        return float(args.timeout)

    if os.getenv(env_key_role) is not None:
        return _coerce_float(os.getenv(env_key_role), default)

    env_global = os.getenv(f"{env_prefix}_TIMEOUT") or os.getenv("LLM_TIMEOUT_SEC")
    if env_global is not None:
        return _coerce_float(env_global, default)

    timeout = _get_timeout_value(agent_cfg)
    if timeout is not None:
        return _coerce_float(timeout, default)

    timeout = _get_timeout_value(global_cfg)
    if timeout is not None:
        return _coerce_float(timeout, default)

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
    default_timeout_sec: float,
) -> AgentConfig:
    global_cfg = _get_global_config(config_file)
    agent_cfg = _get_dict(config_file.get(role))

    provider = (
        getattr(args, f"{role}_provider", None)
        or os.getenv(env_keys.provider)
        or agent_cfg.get("provider")
        or default_provider
    )
    provider = _normalize_provider(str(provider))

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
        env_prefix="METACOGNITION",
        agent_cfg=agent_cfg,
        global_cfg=global_cfg,
        default=default_temperature,
    )
    timeout_sec = _resolve_timeout(
        args=args,
        env_key_role=env_keys.timeout,
        env_prefix="METACOGNITION",
        agent_cfg=agent_cfg,
        global_cfg=global_cfg,
        default=default_timeout_sec,
    )

    return AgentConfig(
        name=name,
        role=role,
        provider=provider,
        model=str(model),
        api_key=str(api_key) if api_key is not None else None,
        base_url=str(base_url) if base_url is not None else None,
        temperature=temperature,
        timeout_sec=timeout_sec,
    )


def _resolve_devui_port(args: argparse.Namespace, config_file: dict[str, Any]) -> int:
    if getattr(args, "port", None) is not None:
        return int(args.port)

    env_port = os.getenv("METACOGNITION_DEVUI_PORT") or os.getenv("DEVUI_PORT")
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
        print(
            f"  環境変数: {config.role.upper()}固有（例: METACOGNITION_{config.role.upper()}_API_KEY） または {provider_env}",
            file=sys.stderr,
        )
    if cli_flag:
        print(f"  CLI: {cli_flag}", file=sys.stderr)
    sys.exit(1)


@dataclass(frozen=True)
class RuntimeConfig:
    config_path: Optional[str]
    devui_port: int
    output_schema: str
    decomposer: AgentConfig
    solver: AgentConfig
    verifier: AgentConfig
    integrator: AgentConfig
    reflector: AgentConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="メタ認知パターン マルチLLM ワークフロー（5段階）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
使用例:
    python main.py "AIに関するブログ記事を書いて"
    python main.py --devui --port 8095
    python main.py --config config.yaml "プロンプト"
    python main.py "REST API設計を作成して" --temperature 0.5

デフォルト値:
    Decomposer: {DECOMPOSER_DEFAULTS.provider}/{DECOMPOSER_DEFAULTS.get_model()}
    Solver:     {SOLVER_DEFAULTS.provider}/{SOLVER_DEFAULTS.get_model()}
    Verifier:   {VERIFIER_DEFAULTS.provider}/{VERIFIER_DEFAULTS.get_model()}
    Integrator: {INTEGRATOR_DEFAULTS.provider}/{INTEGRATOR_DEFAULTS.get_model()}
    Reflector:  {REFLECTOR_DEFAULTS.provider}/{REFLECTOR_DEFAULTS.get_model()}

設定の優先順位: CLI引数 > 環境変数 > 設定ファイル > デフォルト値
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="メタ認知ワークフローで処理するプロンプト",
    )

    # 設定ファイルオプション
    parser.add_argument(
        "--config",
        "-c",
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

    # Decomposer オプション
    parser.add_argument(
        "--decomposer-provider",
        default=None,
        help=f"Decomposerエージェントのプロバイダ (デフォルト: {DECOMPOSER_DEFAULTS.provider})",
    )
    parser.add_argument(
        "--decomposer-model",
        default=None,
        help=f"DecomposerのモデルID (デフォルト: {DECOMPOSER_DEFAULTS.get_model()})",
    )

    # Solver オプション
    parser.add_argument(
        "--solver-provider",
        default=None,
        help=f"Solverエージェントのプロバイダ (デフォルト: {SOLVER_DEFAULTS.provider})",
    )
    parser.add_argument(
        "--solver-model",
        default=None,
        help=f"SolverのモデルID (デフォルト: {SOLVER_DEFAULTS.get_model()})",
    )

    # Verifier オプション
    parser.add_argument(
        "--verifier-provider",
        default=None,
        help=f"Verifierエージェントのプロバイダ (デフォルト: {VERIFIER_DEFAULTS.provider})",
    )
    parser.add_argument(
        "--verifier-model",
        default=None,
        help=f"VerifierのモデルID (デフォルト: {VERIFIER_DEFAULTS.get_model()})",
    )

    # Integrator オプション
    parser.add_argument(
        "--integrator-provider",
        default=None,
        help=f"Integratorエージェントのプロバイダ (デフォルト: {INTEGRATOR_DEFAULTS.provider})",
    )
    parser.add_argument(
        "--integrator-model",
        default=None,
        help=f"IntegratorのモデルID (デフォルト: {INTEGRATOR_DEFAULTS.get_model()})",
    )

    # Reflector オプション
    parser.add_argument(
        "--reflector-provider",
        default=None,
        help=f"Reflectorエージェントのプロバイダ (デフォルト: {REFLECTOR_DEFAULTS.provider})",
    )
    parser.add_argument(
        "--reflector-model",
        default=None,
        help=f"ReflectorのモデルID (デフォルト: {REFLECTOR_DEFAULTS.get_model()})",
    )

    # Provider API keys
    parser.add_argument(
        "--gemini-api-key",
        default=None,
        help="Gemini APIキー (または GEMINI_API_KEY 環境変数を設定)",
    )
    parser.add_argument(
        "--anthropic-api-key",
        default=None,
        help="Anthropic APIキー (または ANTHROPIC_API_KEY 環境変数を設定)",
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
        help=f"全エージェントのtemperature (デフォルト: {DECOMPOSER_DEFAULTS.temperature})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help=f"エージェントごとのタイムアウト秒数 (デフォルト: {DECOMPOSER_DEFAULTS.timeout_sec})",
    )
    parser.add_argument(
        "--output-schema",
        default=None,
        choices=["nested", "flat"],
        help="JSON出力のスキーマ形式 (nested/flat)",
    )

    # プロバイダーランダム選択オプション
    provider_group = parser.add_mutually_exclusive_group()
    provider_group.add_argument(
        "--random-providers",
        action="store_true",
        help="各役割にランダムにプロバイダーを割り当てる（重複あり）",
    )
    provider_group.add_argument(
        "--shuffle-providers",
        action="store_true",
        help="プロバイダーをシャッフルして各役割に割り当てる（役割数に応じて循環）",
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

    output_schema = _resolve_output_schema(args=args, config_file=config_file)

    decomposer_default_provider = DECOMPOSER_DEFAULTS.provider
    solver_default_provider = SOLVER_DEFAULTS.provider
    verifier_default_provider = VERIFIER_DEFAULTS.provider
    integrator_default_provider = INTEGRATOR_DEFAULTS.provider
    reflector_default_provider = REFLECTOR_DEFAULTS.provider

    provider_strategy = _resolve_provider_strategy(args=args, config_file=config_file)
    if provider_strategy == "random":
        (
            decomposer_default_provider,
            solver_default_provider,
            verifier_default_provider,
            integrator_default_provider,
            reflector_default_provider,
        ) = get_random_providers()
    elif provider_strategy == "shuffle":
        (
            decomposer_default_provider,
            solver_default_provider,
            verifier_default_provider,
            integrator_default_provider,
            reflector_default_provider,
        ) = get_shuffled_providers()

    decomposer = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Decomposer",
        role="decomposer",
        env_keys=DECOMPOSER_ENV_KEYS,
        default_provider=decomposer_default_provider,
        default_temperature=DECOMPOSER_DEFAULTS.temperature,
        default_timeout_sec=DECOMPOSER_DEFAULTS.timeout_sec,
    )
    solver = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Solver",
        role="solver",
        env_keys=SOLVER_ENV_KEYS,
        default_provider=solver_default_provider,
        default_temperature=SOLVER_DEFAULTS.temperature,
        default_timeout_sec=SOLVER_DEFAULTS.timeout_sec,
    )
    verifier = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Verifier",
        role="verifier",
        env_keys=VERIFIER_ENV_KEYS,
        default_provider=verifier_default_provider,
        default_temperature=VERIFIER_DEFAULTS.temperature,
        default_timeout_sec=VERIFIER_DEFAULTS.timeout_sec,
    )
    integrator = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Integrator",
        role="integrator",
        env_keys=INTEGRATOR_ENV_KEYS,
        default_provider=integrator_default_provider,
        default_temperature=INTEGRATOR_DEFAULTS.temperature,
        default_timeout_sec=INTEGRATOR_DEFAULTS.timeout_sec,
    )
    reflector = _resolve_agent_config(
        args=args,
        config_file=config_file,
        name="Reflector",
        role="reflector",
        env_keys=REFLECTOR_ENV_KEYS,
        default_provider=reflector_default_provider,
        default_temperature=REFLECTOR_DEFAULTS.temperature,
        default_timeout_sec=REFLECTOR_DEFAULTS.timeout_sec,
    )

    devui_port = _resolve_devui_port(args, config_file)

    return RuntimeConfig(
        config_path=config_path,
        devui_port=devui_port,
        output_schema=output_schema,
        decomposer=decomposer,
        solver=solver,
        verifier=verifier,
        integrator=integrator,
        reflector=reflector,
    )


def print_config_summary(runtime: RuntimeConfig) -> None:
    """解決済みの設定サマリーを出力する（APIキーは表示しない）。"""

    print("\n=== 設定サマリー ===")
    print(f"設定ファイル: {runtime.config_path or '(なし)'}")
    print(f"DevUI Port: {runtime.devui_port}")
    print(f"Output Schema: {runtime.output_schema}")
    print(
        f"Decomposer: {runtime.decomposer.provider}/{runtime.decomposer.model} (temp={runtime.decomposer.temperature}, timeout={runtime.decomposer.timeout_sec}s)"
    )
    print(
        f"Solver:     {runtime.solver.provider}/{runtime.solver.model} (temp={runtime.solver.temperature}, timeout={runtime.solver.timeout_sec}s)"
    )
    print(
        f"Verifier:   {runtime.verifier.provider}/{runtime.verifier.model} (temp={runtime.verifier.temperature}, timeout={runtime.verifier.timeout_sec}s)"
    )
    print(
        f"Integrator: {runtime.integrator.provider}/{runtime.integrator.model} (temp={runtime.integrator.temperature}, timeout={runtime.integrator.timeout_sec}s)"
    )
    print(
        f"Reflector:  {runtime.reflector.provider}/{runtime.reflector.model} (temp={runtime.reflector.temperature}, timeout={runtime.reflector.timeout_sec}s)"
    )
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
    result: MetaCognitionResult,
    verbose: bool = False,
    as_json: bool = False,
    include_raw: bool = False,
    raw_max_chars: int = 8000,
    output_schema: str = "nested",
) -> None:
    """メタ認知結果を読みやすい形式で出力する。"""

    if as_json:
        if output_schema == "flat":
            payload: dict[str, Any] = {
                "original_prompt": result.original_prompt,
                "decomposer_subtasks": result.decomposition.subtasks,
                "decomposer_assumptions": result.decomposition.assumptions,
                "decomposer_constraints": result.decomposition.constraints,
                "decomposer_questions": result.decomposition.questions,
                "decomposer_confidence": result.decomposition.confidence,
                "solver_solutions": [item.model_dump() for item in result.solution.solutions],
                "solver_open_questions": result.solution.open_questions,
                "solver_risks": result.solution.risks,
                "solver_confidence": result.solution.confidence,
                "verifier_issues": result.verification.issues,
                "verifier_corrections": result.verification.corrections,
                "verifier_self_corrections": result.verification.self_corrections,
                "verifier_validation_notes": result.verification.validation_notes,
                "verifier_confidence": result.verification.confidence,
                "integrator_integrated_answer": result.integration.integrated_answer,
                "integrator_applied_corrections": result.integration.applied_corrections,
                "integrator_confidence": result.integration.confidence,
                "reflector_final_response": result.reflection.final_response,
                "reflector_confidence_score": result.reflection.confidence_score,
                "reflector_uncertainties": result.reflection.uncertainties,
                "reflector_self_corrections": result.reflection.self_corrections,
                "reflector_reflection_notes": result.reflection.reflection_notes,
                "total_duration_sec": result.total_duration_sec,
                "decomposer_model": result.decomposer_model,
                "solver_model": result.solver_model,
                "verifier_model": result.verifier_model,
                "integrator_model": result.integrator_model,
                "reflector_model": result.reflector_model,
            }
            if include_raw and result.raw is not None:
                payload["raw"] = result.raw.model_dump()
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            exclude = {} if include_raw else {"raw"}
            payload = result.model_dump(exclude_none=True, exclude=exclude)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if not verbose:
        print(result.reflection.final_response)
        return

    print("\n" + "=" * 70)
    print("メタ認知 ワークフロー 結果（5段階）")
    print("=" * 70)

    print("\n--- 元のプロンプト ---")
    print(result.original_prompt)

    print("\n--- ステージ1: 分解 (Decomposer) ---")
    print(f"モデル: {result.decomposer_model}")
    print(f"確信度: {result.decomposition.confidence:.2f}")
    print("サブタスク:")
    for s in result.decomposition.subtasks:
        print(f"  - {s}")
    print("前提:")
    for a in result.decomposition.assumptions:
        print(f"  - {a}")
    print("制約:")
    for c in result.decomposition.constraints:
        print(f"  - {c}")
    print("確認事項:")
    for q in result.decomposition.questions:
        print(f"  - {q}")

    print("\n--- ステージ2: 解決 (Solver) ---")
    print(f"モデル: {result.solver_model}")
    print(f"確信度: {result.solution.confidence:.2f}")
    print("解決案:")
    for item in result.solution.solutions:
        print(f"  * {item.subtask}: {item.answer}")
    print("未解決事項:")
    for q in result.solution.open_questions:
        print(f"  - {q}")
    print("リスク:")
    for r in result.solution.risks:
        print(f"  - {r}")

    print("\n--- ステージ3: 検証 (Verifier) ---")
    print(f"モデル: {result.verifier_model}")
    print(f"確信度: {result.verification.confidence:.2f}")
    print("問題点:")
    for issue in result.verification.issues:
        print(f"  - {issue}")
    print("修正案:")
    for corr in result.verification.corrections:
        print(f"  - {corr}")
    print("自律修正:")
    for sc in result.verification.self_corrections:
        print(f"  - {sc}")
    print("検証メモ:")
    for note in result.verification.validation_notes:
        print(f"  - {note}")

    print("\n--- ステージ4: 統合 (Integrator) ---")
    print(f"モデル: {result.integrator_model}")
    print(f"確信度: {result.integration.confidence:.2f}")
    print("反映した修正点:")
    for imp in result.integration.applied_corrections:
        print(f"  - {imp}")
    print("統合回答草案:")
    print(result.integration.integrated_answer)

    print("\n--- ステージ5: 反省 (Reflector) ---")
    print(f"モデル: {result.reflector_model}")
    print(f"確信度スコア: {result.reflection.confidence_score:.2f}")
    print("不確実性:")
    for u in result.reflection.uncertainties:
        print(f"  - {u}")
    print("自律修正:")
    for sc in result.reflection.self_corrections:
        print(f"  - {sc}")
    print("反省:")
    for note in result.reflection.reflection_notes:
        print(f"  - {note}")

    print("\n### 最終コンテンツ ###\n")
    print(result.reflection.final_response)

    print("\n" + "-" * 70)
    print(f"総処理時間: {result.total_duration_sec:.2f}秒")
    print("=" * 70)

    if include_raw:
        print("\n--- RAWデータ (サニタイズ済み) ---")
        raw_data = result.raw.model_dump() if result.raw is not None else {}
        raw_data_view = _truncate_strings(raw_data, raw_max_chars)
        print(json.dumps(raw_data_view, ensure_ascii=False, indent=2))


def _extract_metacognition_result(run_result: object) -> MetaCognitionResult | None:
    """workflow.run()の戻り値からMetaCognitionResultを抽出する。"""

    if isinstance(run_result, MetaCognitionResult):
        return run_result

    outputs: list[object] = []

    if WorkflowRunResult is not None and isinstance(run_result, WorkflowRunResult):
        outputs = run_result.get_outputs()
    elif isinstance(run_result, list):
        for event in run_result:
            data = getattr(event, "data", None)
            if data is not None:
                outputs.append(data)

    for candidate in reversed(outputs):
        if isinstance(candidate, MetaCognitionResult):
            return candidate
        try:
            return MetaCognitionResult.model_validate(candidate)
        except Exception:
            continue

    return None


async def run_cli(args: argparse.Namespace, runtime: RuntimeConfig) -> None:
    """CLIモードでワークフローを実行する。"""

    if not args.prompt:
        print("エラー: CLIモードではプロンプトが必要です")
        print("使用方法: python main.py 'ここにプロンプトを入力'")
        sys.exit(1)

    _require_api_key(runtime.decomposer)
    _require_api_key(runtime.solver)
    _require_api_key(runtime.verifier)
    _require_api_key(runtime.integrator)
    _require_api_key(runtime.reflector)

    decomposer_config = runtime.decomposer
    solver_config = runtime.solver
    verifier_config = runtime.verifier
    integrator_config = runtime.integrator
    reflector_config = runtime.reflector

    log_stream = sys.stderr if args.json else sys.stdout
    if args.verbose:
        print("\nメタ認知ワークフローを開始しています...", file=log_stream)
        print(f"  Decomposer: {decomposer_config.provider}/{decomposer_config.model}", file=log_stream)
        print(f"  Solver: {solver_config.provider}/{solver_config.model}", file=log_stream)
        print(f"  Verifier: {verifier_config.provider}/{verifier_config.model}", file=log_stream)
        print(f"  Integrator: {integrator_config.provider}/{integrator_config.model}", file=log_stream)
        print(f"  Reflector: {reflector_config.provider}/{reflector_config.model}", file=log_stream)
        print(file=log_stream)

    workflow = build_metacognition_workflow(
        decomposer_config=decomposer_config,
        solver_config=solver_config,
        verifier_config=verifier_config,
        integrator_config=integrator_config,
        reflector_config=reflector_config,
    )

    run_result = await workflow.run(args.prompt)
    reflection_result = _extract_metacognition_result(run_result)

    if reflection_result is None:
        print(f"エラー: MetaCognitionResultを抽出できませんでした: {type(run_result)}", file=sys.stderr)
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
        output_schema=runtime.output_schema,
    )


def run_devui(args: argparse.Namespace, runtime: RuntimeConfig) -> None:
    """DevUIモードでワークフローを実行する。"""
    print("エラー: DevUIは軽量エンジンではサポートされていません。CLIをご利用ください。")
    sys.exit(1)


def main() -> None:
    load_dotenv()
    args = parse_args()

    runtime = get_runtime_config(args)

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
