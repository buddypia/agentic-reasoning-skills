"""リフレクションパターン 設定管理（5段階）。

設定の優先順位 (高い順):
    1. CLI引数
    2. 環境変数 (REFLECTION_<ROLE>_<KEY> or <PROVIDER>_API_KEY)
    3. 設定ファイル (config.yaml / config.json など)
    4. デフォルト値
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Any, Optional

from .config import AgentConfig


# =============================================================================
# Default Model IDs by Provider
# =============================================================================

DEFAULT_MODELS: dict[str, str] = {
    # Google Gemini: Antigravity CLI 기본 (Gemini 3.5 Flash, 2026-05)
    "gemini": "gemini-3.5-flash",
    # Anthropic Claude: Claude Code CLI 최신 (2026-05)
    "anthropic": "claude-opus-4-8",
    "claude": "claude-opus-4-8",
    # OpenAI: Codex CLI 최신 flagship (2026-04)
    "openai": "gpt-5.5",
    # Mock provider (offline smoke tests)
    "mock": "mock-v1",
}

# Available providers for random assignment
AVAILABLE_PROVIDERS: list[str] = ["gemini", "anthropic", "openai"]


def get_random_providers() -> tuple[str, str, str, str, str]:
    """ランダムに5つの役割にプロバイダーを割り当てる（重複あり）。"""

    return (
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
    )


def get_shuffled_providers() -> tuple[str, str, str, str, str]:
    """プロバイダーをシャッフルして5つの役割に割り当てる。

    3プロバイダーを一度シャッフルして順に割り当て、役割数が多い分は循環させる。
    """

    providers = AVAILABLE_PROVIDERS.copy()
    random.shuffle(providers)
    assigned = [providers[i % len(providers)] for i in range(5)]
    return (assigned[0], assigned[1], assigned[2], assigned[3], assigned[4])


# =============================================================================
# Default Agent Settings
# =============================================================================


@dataclass
class DefaultAgentSettings:
    """デフォルトのエージェント設定"""

    provider: str
    model: Optional[str] = None
    temperature: float = 0.7
    timeout_sec: float = 120.0

    def get_model(self) -> str:
        """モデルIDを取得（設定がない場合はプロバイダーのデフォルトを使用）"""

        if self.model:
            return self.model
        normalized = self.provider.strip().lower()
        return DEFAULT_MODELS.get(normalized, "gpt-5.5")


DECOMPOSER_DEFAULTS = DefaultAgentSettings(provider="gemini", model="gemini-3.5-flash")
SOLVER_DEFAULTS = DefaultAgentSettings(provider="gemini", model="gemini-3.5-flash")
VERIFIER_DEFAULTS = DefaultAgentSettings(provider="anthropic", model="claude-opus-4-8")
INTEGRATOR_DEFAULTS = DefaultAgentSettings(provider="openai", model="gpt-5.5")
REFLECTOR_DEFAULTS = DefaultAgentSettings(provider="openai", model="gpt-5.5")


# =============================================================================
# Environment Variable Keys
# =============================================================================


@dataclass
class EnvVarKeys:
    """環境変数キーの定義"""

    provider: str
    model: str
    api_key: str
    base_url: str
    temperature: str
    timeout: str

    provider_api_key: str
    provider_model: str


DECOMPOSER_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_DECOMPOSER_PROVIDER",
    model="REFLECTION_DECOMPOSER_MODEL",
    api_key="REFLECTION_DECOMPOSER_API_KEY",
    base_url="REFLECTION_DECOMPOSER_BASE_URL",
    temperature="REFLECTION_DECOMPOSER_TEMPERATURE",
    timeout="REFLECTION_DECOMPOSER_TIMEOUT",
    provider_api_key="GEMINI_API_KEY",
    provider_model="GEMINI_MODEL_ID",
)

SOLVER_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_SOLVER_PROVIDER",
    model="REFLECTION_SOLVER_MODEL",
    api_key="REFLECTION_SOLVER_API_KEY",
    base_url="REFLECTION_SOLVER_BASE_URL",
    temperature="REFLECTION_SOLVER_TEMPERATURE",
    timeout="REFLECTION_SOLVER_TIMEOUT",
    provider_api_key="GEMINI_API_KEY",
    provider_model="GEMINI_MODEL_ID",
)

VERIFIER_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_VERIFIER_PROVIDER",
    model="REFLECTION_VERIFIER_MODEL",
    api_key="REFLECTION_VERIFIER_API_KEY",
    base_url="REFLECTION_VERIFIER_BASE_URL",
    temperature="REFLECTION_VERIFIER_TEMPERATURE",
    timeout="REFLECTION_VERIFIER_TIMEOUT",
    provider_api_key="ANTHROPIC_API_KEY",
    provider_model="ANTHROPIC_MODEL_ID",
)

INTEGRATOR_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_INTEGRATOR_PROVIDER",
    model="REFLECTION_INTEGRATOR_MODEL",
    api_key="REFLECTION_INTEGRATOR_API_KEY",
    base_url="REFLECTION_INTEGRATOR_BASE_URL",
    temperature="REFLECTION_INTEGRATOR_TEMPERATURE",
    timeout="REFLECTION_INTEGRATOR_TIMEOUT",
    provider_api_key="OPENAI_API_KEY",
    provider_model="OPENAI_CHAT_MODEL_ID",
)

REFLECTOR_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_REFLECTOR_PROVIDER",
    model="REFLECTION_REFLECTOR_MODEL",
    api_key="REFLECTION_REFLECTOR_API_KEY",
    base_url="REFLECTION_REFLECTOR_BASE_URL",
    temperature="REFLECTION_REFLECTOR_TEMPERATURE",
    timeout="REFLECTION_REFLECTOR_TIMEOUT",
    provider_api_key="OPENAI_API_KEY",
    provider_model="OPENAI_CHAT_MODEL_ID",
)


# =============================================================================
# Settings Resolver
# =============================================================================


def get_env(key: str, default: Any = None) -> Any:
    """環境変数を取得"""

    return os.getenv(key, default)


def get_env_float(key: str, default: float) -> float:
    """環境変数をfloatとして取得"""

    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def resolve_provider_api_key(provider: str) -> tuple[str, str]:
    """プロバイダーに基づいてAPI KEY環境変数名を解決"""

    normalized = provider.strip().lower()
    if normalized == "gemini":
        return "GEMINI_API_KEY", "GEMINI_MODEL_ID"
    if normalized in {"anthropic", "claude"}:
        return "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL_ID"
    if normalized == "openai":
        return "OPENAI_API_KEY", "OPENAI_CHAT_MODEL_ID"
    if normalized == "mock":
        return "", ""
    return "", ""


def resolve_api_key_for_provider(provider: str, role_api_key_env: str) -> Optional[str]:
    """プロバイダーに基づいてAPIキーを解決

    優先順位:
        1. ロール固有の環境変数 (REFLECTION_<ROLE>_API_KEY)
        2. プロバイダー固有の環境変数 (<PROVIDER>_API_KEY)
    """

    role_key = get_env(role_api_key_env)
    if role_key:
        return role_key

    provider_key_env, _ = resolve_provider_api_key(provider)
    return get_env(provider_key_env)


def create_agent_config_from_env(
    name: str,
    role: str,
    env_keys: EnvVarKeys,
    defaults: DefaultAgentSettings,
    config_file: Optional[dict[str, Any]] = None,
) -> AgentConfig:
    """環境変数と設定ファイルからAgentConfigを作成"""

    if config_file is None:
        config_file = {}

    agent_config = config_file.get(role, {})
    global_config = config_file.get("global", {}) or config_file.get("common", {})

    def get_value(key: str, env_key: str, default: Any) -> Any:
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val
        if isinstance(agent_config, dict) and key in agent_config:
            return agent_config[key]
        if isinstance(global_config, dict) and key in global_config:
            return global_config[key]
        return default

    provider = get_value("provider", env_keys.provider, defaults.provider)

    model_from_env = os.getenv(env_keys.model)
    if model_from_env:
        model = model_from_env
    else:
        _, provider_model_env = resolve_provider_api_key(provider)
        model_from_provider = os.getenv(provider_model_env)
        if model_from_provider:
            model = model_from_provider
        elif isinstance(agent_config, dict) and "model" in agent_config:
            model = agent_config["model"]
        else:
            model = DEFAULT_MODELS.get(provider.strip().lower(), "gpt-5.5")

    api_key = resolve_api_key_for_provider(provider, env_keys.api_key)
    if not api_key and isinstance(agent_config, dict):
        api_key = agent_config.get("api_key")

    base_url = get_value("base_url", env_keys.base_url, None)
    if provider.strip().lower() == "openai" and not base_url:
        base_url = os.getenv("OPENAI_BASE_URL")

    temperature_str = get_value("temperature", env_keys.temperature, str(defaults.temperature))
    timeout_str = get_value("timeout", env_keys.timeout, str(defaults.timeout_sec))

    try:
        temperature = float(temperature_str)
    except (ValueError, TypeError):
        temperature = defaults.temperature

    try:
        timeout_sec = float(timeout_str)
    except (ValueError, TypeError):
        timeout_sec = defaults.timeout_sec

    return AgentConfig(
        name=name,
        role=role,
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        timeout_sec=timeout_sec,
    )


def create_default_configs(
    config_file: Optional[dict[str, Any]] = None,
) -> tuple[AgentConfig, AgentConfig, AgentConfig, AgentConfig, AgentConfig]:
    """デフォルト設定で5つのエージェントのAgentConfigを作成"""

    decomposer = create_agent_config_from_env(
        name="Decomposer",
        role="decomposer",
        env_keys=DECOMPOSER_ENV_KEYS,
        defaults=DECOMPOSER_DEFAULTS,
        config_file=config_file,
    )

    solver = create_agent_config_from_env(
        name="Solver",
        role="solver",
        env_keys=SOLVER_ENV_KEYS,
        defaults=SOLVER_DEFAULTS,
        config_file=config_file,
    )

    verifier = create_agent_config_from_env(
        name="Verifier",
        role="verifier",
        env_keys=VERIFIER_ENV_KEYS,
        defaults=VERIFIER_DEFAULTS,
        config_file=config_file,
    )

    integrator = create_agent_config_from_env(
        name="Integrator",
        role="integrator",
        env_keys=INTEGRATOR_ENV_KEYS,
        defaults=INTEGRATOR_DEFAULTS,
        config_file=config_file,
    )

    reflector = create_agent_config_from_env(
        name="Reflector",
        role="reflector",
        env_keys=REFLECTOR_ENV_KEYS,
        defaults=REFLECTOR_DEFAULTS,
        config_file=config_file,
    )

    return decomposer, solver, verifier, integrator, reflector


def print_config_info() -> None:
    """設定の優先順位と環境変数名を表示"""

    print(
        """
設定の優先順位 (高い順):
    1. CLI引数 (--decomposer-model, --temperature, etc.)
    2. 環境変数
    3. 設定ファイル
    4. デフォルト値

設定ファイル:
    - --config PATH で明示指定
    - または CONFIG_FILE 環境変数
    - または自動探索: config.yaml / config.yml / config.json / .config.yaml / .config.yml / .config.json
    - --no-config で無効化

環境変数:
    [プロバイダー割当戦略]
    REFLECTION_PROVIDER_STRATEGY  : fixed / random / shuffle
    REFLECTION_PROVIDER_MODE      : 上記のエイリアス
    REFLECTION_RANDOM_PROVIDERS   : true/1/yes で random と同等
    REFLECTION_SHUFFLE_PROVIDERS  : true/1/yes で shuffle と同等

    [出力スキーマ]
    REFLECTION_OUTPUT_SCHEMA  : nested / flat

    [APIキー]
    GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY
    OPENAI_BASE_URL (OpenAIのbase_url)

    [モデルID]
    GEMINI_MODEL_ID / ANTHROPIC_MODEL_ID / OPENAI_CHAT_MODEL_ID

    [Decomposer (分解)]
    REFLECTION_DECOMPOSER_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_DECOMPOSER_MODEL     : モデルID
    REFLECTION_DECOMPOSER_API_KEY   : APIキー (または GEMINI_API_KEY)
    REFLECTION_DECOMPOSER_BASE_URL  : base_url (主にOpenAI向け)
    REFLECTION_DECOMPOSER_TEMPERATURE: 温度
    REFLECTION_DECOMPOSER_TIMEOUT    : タイムアウト（秒）

    [Solver (解決)]
    REFLECTION_SOLVER_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_SOLVER_MODEL     : モデルID
    REFLECTION_SOLVER_API_KEY   : APIキー (または GEMINI_API_KEY)
    REFLECTION_SOLVER_BASE_URL  : base_url (主にOpenAI向け)
    REFLECTION_SOLVER_TEMPERATURE: 温度
    REFLECTION_SOLVER_TIMEOUT    : タイムアウト（秒）

    [Verifier (検証)]
    REFLECTION_VERIFIER_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_VERIFIER_MODEL     : モデルID
    REFLECTION_VERIFIER_API_KEY   : APIキー (または ANTHROPIC_API_KEY)
    REFLECTION_VERIFIER_BASE_URL  : base_url (主にOpenAI向け)
    REFLECTION_VERIFIER_TEMPERATURE: 温度
    REFLECTION_VERIFIER_TIMEOUT    : タイムアウト（秒）

    [Integrator (統合)]
    REFLECTION_INTEGRATOR_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_INTEGRATOR_MODEL     : モデルID
    REFLECTION_INTEGRATOR_API_KEY   : APIキー (または OPENAI_API_KEY)
    REFLECTION_INTEGRATOR_BASE_URL  : base_url (または OPENAI_BASE_URL)
    REFLECTION_INTEGRATOR_TEMPERATURE: 温度
    REFLECTION_INTEGRATOR_TIMEOUT    : タイムアウト（秒）

    [Reflector (反省)]
    REFLECTION_REFLECTOR_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_REFLECTOR_MODEL     : モデルID
    REFLECTION_REFLECTOR_API_KEY   : APIキー (または OPENAI_API_KEY)
    REFLECTION_REFLECTOR_BASE_URL  : base_url (または OPENAI_BASE_URL)
    REFLECTION_REFLECTOR_TEMPERATURE: 温度
    REFLECTION_REFLECTOR_TIMEOUT    : タイムアウト（秒）

    [共通パラメータ（全ロールに適用。ロール別より低優先）]
    REFLECTION_TEMPERATURE       : 温度 (または LLM_TEMPERATURE)
    REFLECTION_TIMEOUT           : タイムアウト秒 (または LLM_TIMEOUT_SEC)
    REFLECTION_DEVUI_PORT        : DevUIポート (または DEVUI_PORT)

デフォルト値:
    Decomposer: gemini / gemini-3.5-flash
    Solver:    gemini / gemini-3.5-flash
    Verifier:  anthropic / claude-opus-4-8
    Integrator: openai / gpt-5.5
    Reflector:  openai / gpt-5.5
"""
    )
