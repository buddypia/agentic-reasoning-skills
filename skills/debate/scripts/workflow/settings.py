"""討論パターン 設定管理。

設定の優先順位 (高い順):
    1. CLI引数
    2. 環境変数 (DEBATE_<ROLE>_<KEY> or <PROVIDER>_API_KEY)
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


def get_random_providers() -> tuple[str, str, str]:
    """ランダムに3つの役割にプロバイダーを割り当てる（重複あり）。

    Returns:
        (proponent_provider, opponent_provider, moderator_provider)
    """
    return (
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
    )


def get_shuffled_providers() -> tuple[str, str, str]:
    """3つのプロバイダーをシャッフルして各役割に割り当てる（重複なし）。

    Returns:
        (proponent_provider, opponent_provider, moderator_provider)
    """
    providers = AVAILABLE_PROVIDERS.copy()
    random.shuffle(providers)
    return (providers[0], providers[1], providers[2])


# =============================================================================
# Default Agent Settings
# =============================================================================

@dataclass
class DefaultAgentSettings:
    """デフォルトのエージェント設定"""
    provider: str
    model: Optional[str] = None
    temperature: float = 0.7

    def get_model(self) -> str:
        """モデルIDを取得（設定がない場合はプロバイダーのデフォルトを使用）"""
        if self.model:
            return self.model
        normalized = self.provider.strip().lower()
        return DEFAULT_MODELS.get(normalized, "gpt-5.5")


# Default configurations for each agent role
PROPONENT_DEFAULTS = DefaultAgentSettings(provider="gemini")
OPPONENT_DEFAULTS = DefaultAgentSettings(provider="anthropic")
MODERATOR_DEFAULTS = DefaultAgentSettings(provider="openai")


# =============================================================================
# Environment Variable Keys
# =============================================================================

@dataclass
class EnvVarKeys:
    """環境変数キーの定義"""
    # Role-specific environment variables
    provider: str
    model: str
    api_key: str
    base_url: str
    temperature: str

    # Provider-specific fallback keys for API
    provider_api_key: str
    provider_model: str


PROPONENT_ENV_KEYS = EnvVarKeys(
    provider="DEBATE_PROPONENT_PROVIDER",
    model="DEBATE_PROPONENT_MODEL",
    api_key="DEBATE_PROPONENT_API_KEY",
    base_url="DEBATE_PROPONENT_BASE_URL",
    temperature="DEBATE_PROPONENT_TEMPERATURE",
    provider_api_key="GEMINI_API_KEY",
    provider_model="GEMINI_MODEL_ID",
)

OPPONENT_ENV_KEYS = EnvVarKeys(
    provider="DEBATE_OPPONENT_PROVIDER",
    model="DEBATE_OPPONENT_MODEL",
    api_key="DEBATE_OPPONENT_API_KEY",
    base_url="DEBATE_OPPONENT_BASE_URL",
    temperature="DEBATE_OPPONENT_TEMPERATURE",
    provider_api_key="ANTHROPIC_API_KEY",
    provider_model="ANTHROPIC_MODEL_ID",
)

MODERATOR_ENV_KEYS = EnvVarKeys(
    provider="DEBATE_MODERATOR_PROVIDER",
    model="DEBATE_MODERATOR_MODEL",
    api_key="DEBATE_MODERATOR_API_KEY",
    base_url="DEBATE_MODERATOR_BASE_URL",
    temperature="DEBATE_MODERATOR_TEMPERATURE",
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
    elif normalized in {"anthropic", "claude"}:
        return "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL_ID"
    elif normalized == "openai":
        return "OPENAI_API_KEY", "OPENAI_CHAT_MODEL_ID"
    elif normalized == "mock":
        return "", ""
    return "", ""


def resolve_api_key_for_provider(provider: str, role_api_key_env: str) -> Optional[str]:
    """プロバイダーに基づいてAPIキーを解決

    優先順位:
        1. ロール固有の環境変数 (DEBATE_<ROLE>_API_KEY)
        2. プロバイダー固有の環境変数 (<PROVIDER>_API_KEY)
    """
    # First try role-specific key
    role_key = get_env(role_api_key_env)
    if role_key:
        return role_key

    # Fallback to provider-specific key
    provider_key_env, _ = resolve_provider_api_key(provider)
    return get_env(provider_key_env)


def create_agent_config_from_env(
    name: str,
    role: str,
    env_keys: EnvVarKeys,
    defaults: DefaultAgentSettings,
    config_file: Optional[dict[str, Any]] = None,
) -> AgentConfig:
    """環境変数と設定ファイルからAgentConfigを作成

    Args:
        name: エージェント名
        role: エージェントの役割
        env_keys: 環境変数キーの定義
        defaults: デフォルト設定
        config_file: 設定ファイルから読み込んだ値（オプション）

    Returns:
        AgentConfig instance
    """
    if config_file is None:
        config_file = {}

    agent_config = config_file.get(role, {})
    global_config = config_file.get("global", {})

    def get_value(key: str, env_key: str, default: Any) -> Any:
        """設定値を取得（環境変数 > 設定ファイル > デフォルト）"""
        # Environment variable first
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val

        # Then agent-specific config
        if isinstance(agent_config, dict) and key in agent_config:
            return agent_config[key]

        # Then global config
        if isinstance(global_config, dict) and key in global_config:
            return global_config[key]

        # Finally default
        return default

    # Resolve provider
    provider = get_value("provider", env_keys.provider, defaults.provider)

    # Resolve model
    model_from_env = os.getenv(env_keys.model)
    if model_from_env:
        model = model_from_env
    else:
        # Check provider-specific model env var
        _, provider_model_env = resolve_provider_api_key(provider)
        model_from_provider = os.getenv(provider_model_env)
        if model_from_provider:
            model = model_from_provider
        elif isinstance(agent_config, dict) and "model" in agent_config:
            model = agent_config["model"]
        else:
            # Use provider default
            model = DEFAULT_MODELS.get(provider.strip().lower(), "gpt-5.5")

    # Resolve API key
    api_key = resolve_api_key_for_provider(provider, env_keys.api_key)
    if not api_key and isinstance(agent_config, dict):
        api_key = agent_config.get("api_key")

    # Resolve base_url (env > config > default)
    base_url = os.getenv(env_keys.base_url)
    if provider.strip().lower() == "openai":
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
    if base_url is None:
        if isinstance(agent_config, dict) and "base_url" in agent_config:
            base_url = agent_config.get("base_url")
        elif isinstance(global_config, dict) and "base_url" in global_config:
            base_url = global_config.get("base_url")

    # Resolve numeric values
    temperature_str = get_value("temperature", env_keys.temperature, str(defaults.temperature))

    try:
        temperature = float(temperature_str)
    except (ValueError, TypeError):
        temperature = defaults.temperature

    return AgentConfig(
        name=name,
        role=role,
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )


def create_default_configs(
    config_file: Optional[dict[str, Any]] = None,
) -> tuple[AgentConfig, AgentConfig, AgentConfig]:
    """デフォルト設定で3つのエージェントのAgentConfigを作成

    Args:
        config_file: 設定ファイルから読み込んだ値（オプション）

    Returns:
        (proponent_config, opponent_config, moderator_config)
    """
    proponent = create_agent_config_from_env(
        name="Proponent",
        role="proponent",
        env_keys=PROPONENT_ENV_KEYS,
        defaults=PROPONENT_DEFAULTS,
        config_file=config_file,
    )

    opponent = create_agent_config_from_env(
        name="Opponent",
        role="opponent",
        env_keys=OPPONENT_ENV_KEYS,
        defaults=OPPONENT_DEFAULTS,
        config_file=config_file,
    )

    moderator = create_agent_config_from_env(
        name="Moderator",
        role="moderator",
        env_keys=MODERATOR_ENV_KEYS,
        defaults=MODERATOR_DEFAULTS,
        config_file=config_file,
    )

    return proponent, opponent, moderator


def print_config_info() -> None:
    """設定の優先順位と環境変数名を表示"""
    print("""
設定の優先順位 (高い順):
    1. CLI引数 (--proponent-model, --temperature, etc.)
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
    DEBATE_PROVIDER_STRATEGY  : fixed / random / shuffle
    DEBATE_PROVIDER_MODE      : 上記のエイリアス
    DEBATE_RANDOM_PROVIDERS   : true/1/yes で random と同等
    DEBATE_SHUFFLE_PROVIDERS  : true/1/yes で shuffle と同等

    [APIキー]
    GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY
    OPENAI_BASE_URL (OpenAIのbase_url)
    ※ mock プロバイダーはAPIキー不要

    [モデルID]
    GEMINI_MODEL_ID / ANTHROPIC_MODEL_ID / OPENAI_CHAT_MODEL_ID

    [Proponent (賛成派)]
    DEBATE_PROPONENT_PROVIDER  : プロバイダー (gemini/anthropic/openai/mock)
    DEBATE_PROPONENT_MODEL     : モデルID
    DEBATE_PROPONENT_API_KEY   : APIキー (または GEMINI_API_KEY)
    DEBATE_PROPONENT_BASE_URL  : base_url (主にOpenAI向け)
    DEBATE_PROPONENT_TEMPERATURE: 温度

    [Opponent (反対派)]
    DEBATE_OPPONENT_PROVIDER   : プロバイダー (gemini/anthropic/openai/mock)
    DEBATE_OPPONENT_MODEL      : モデルID
    DEBATE_OPPONENT_API_KEY    : APIキー (または ANTHROPIC_API_KEY)
    DEBATE_OPPONENT_BASE_URL   : base_url (主にOpenAI向け)
    DEBATE_OPPONENT_TEMPERATURE : 温度

    [Moderator (中立派)]
    DEBATE_MODERATOR_PROVIDER  : プロバイダー (gemini/anthropic/openai/mock)
    DEBATE_MODERATOR_MODEL     : モデルID
    DEBATE_MODERATOR_API_KEY   : APIキー (または OPENAI_API_KEY)
    DEBATE_MODERATOR_BASE_URL  : base_url (または OPENAI_BASE_URL)
    DEBATE_MODERATOR_TEMPERATURE: 温度

    [共通パラメータ（全ロールに適用。ロール別より低優先）]
    DEBATE_TEMPERATURE       : 温度 (または LLM_TEMPERATURE)
    DEBATE_DEVUI_PORT        : DevUIポート (または DEVUI_PORT)

デフォルト値:
    Proponent: gemini / gemini-3.5-flash
    Opponent:  anthropic / claude-opus-4-8
    Moderator: openai / gpt-5.5
""")
