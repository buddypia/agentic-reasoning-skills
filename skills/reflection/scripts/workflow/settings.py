"""リフレクションパターン 設定管理。

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
# Available Providers
# =============================================================================

AVAILABLE_PROVIDERS: list[str] = ["gemini", "anthropic", "openai"]


def get_random_providers() -> tuple[str, str, str]:
    """ランダムに3つの役割にプロバイダーを割り当てる（重複あり）。"""
    return (
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
        random.choice(AVAILABLE_PROVIDERS),
    )


def get_shuffled_providers() -> tuple[str, str, str]:
    """3つのプロバイダーをシャッフルして各役割に割り当てる（重複なし）。"""
    providers = AVAILABLE_PROVIDERS.copy()
    random.shuffle(providers)
    return (providers[0], providers[1], providers[2])


# =============================================================================
# Default Model IDs by Provider
# =============================================================================

DEFAULT_MODELS: dict[str, str] = {
    # Google Gemini: Most intelligent (as of 2026-01)
    "gemini": "gemini-3-pro-preview",
    # Anthropic Claude: Most capable (as of 2026-01)
    "anthropic": "claude-opus-4-1-20250805",
    "claude": "claude-opus-4-1-20250805",
    # OpenAI: Latest flagship (as of 2026-01)
    "openai": "gpt-5.2",
    # Mock provider (offline smoke tests)
    "mock": "mock-v1",
}


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
        return DEFAULT_MODELS.get(normalized, "gpt-5.2")


# Default configurations for each agent role
GENERATOR_DEFAULTS = DefaultAgentSettings(provider="gemini", model="gemini-3-pro-preview")
CRITIC_DEFAULTS = DefaultAgentSettings(provider="anthropic", model="claude-opus-4-1-20250805")
REFINER_DEFAULTS = DefaultAgentSettings(provider="openai", model="gpt-5.2")


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


GENERATOR_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_GENERATOR_PROVIDER",
    model="REFLECTION_GENERATOR_MODEL",
    api_key="REFLECTION_GENERATOR_API_KEY",
    base_url="REFLECTION_GENERATOR_BASE_URL",
    temperature="REFLECTION_GENERATOR_TEMPERATURE",
    provider_api_key="GEMINI_API_KEY",
    provider_model="GEMINI_MODEL_ID",
)

CRITIC_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_CRITIC_PROVIDER",
    model="REFLECTION_CRITIC_MODEL",
    api_key="REFLECTION_CRITIC_API_KEY",
    base_url="REFLECTION_CRITIC_BASE_URL",
    temperature="REFLECTION_CRITIC_TEMPERATURE",
    provider_api_key="ANTHROPIC_API_KEY",
    provider_model="ANTHROPIC_MODEL_ID",
)

REFINER_ENV_KEYS = EnvVarKeys(
    provider="REFLECTION_REFINER_PROVIDER",
    model="REFLECTION_REFINER_MODEL",
    api_key="REFLECTION_REFINER_API_KEY",
    base_url="REFLECTION_REFINER_BASE_URL",
    temperature="REFLECTION_REFINER_TEMPERATURE",
    provider_api_key="OPENAI_API_KEY",
    provider_model="OPENAI_CHAT_MODEL_ID",
)


# =============================================================================
# Settings Resolver
# =============================================================================

def get_env(key: str, default: Any = None) -> Any:
    """環境変数を取得"""
    return os.getenv(key, default)


def select_random_provider(
    available_providers: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> str:
    """利用可能なプロバイダーからランダムに1つを選択する。

    Args:
        available_providers: 選択対象のプロバイダーリスト（デフォルト: AVAILABLE_PROVIDERS）
        exclude: 除外するプロバイダーのリスト

    Returns:
        選択されたプロバイダー名
    """
    providers = available_providers or AVAILABLE_PROVIDERS.copy()
    if exclude:
        providers = [p for p in providers if p not in exclude]
    if not providers:
        providers = AVAILABLE_PROVIDERS.copy()
    return random.choice(providers)


def resolve_provider_with_random(
    provider: Optional[str],
    default_provider: str,
    available_providers: Optional[list[str]] = None,
) -> str:
    """プロバイダーを解決する。'random'の場合はランダム選択する。

    Args:
        provider: 指定されたプロバイダー（None, 'random', または具体的なプロバイダー名）
        default_provider: デフォルトのプロバイダー
        available_providers: ランダム選択時の対象プロバイダーリスト

    Returns:
        解決されたプロバイダー名
    """
    if provider is None:
        return default_provider

    normalized = provider.strip().lower()
    if normalized == "random":
        return select_random_provider(available_providers)

    return normalized


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
        1. ロール固有の環境変数 (REFLECTION_<ROLE>_API_KEY)
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
    global_config = config_file.get("global", {}) or config_file.get("common", {})

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
            model = DEFAULT_MODELS.get(provider.strip().lower(), "gpt-5.2")

    # Resolve API key
    api_key = resolve_api_key_for_provider(provider, env_keys.api_key)
    if not api_key and isinstance(agent_config, dict):
        api_key = agent_config.get("api_key")

    # Resolve base_url
    base_url = get_value("base_url", env_keys.base_url, None)
    if provider.strip().lower() == "openai" and not base_url:
        base_url = os.getenv("OPENAI_BASE_URL")

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
        (generator_config, critic_config, refiner_config)
    """
    generator = create_agent_config_from_env(
        name="Generator",
        role="generator",
        env_keys=GENERATOR_ENV_KEYS,
        defaults=GENERATOR_DEFAULTS,
        config_file=config_file,
    )

    critic = create_agent_config_from_env(
        name="Critic",
        role="critic",
        env_keys=CRITIC_ENV_KEYS,
        defaults=CRITIC_DEFAULTS,
        config_file=config_file,
    )

    refiner = create_agent_config_from_env(
        name="Refiner",
        role="refiner",
        env_keys=REFINER_ENV_KEYS,
        defaults=REFINER_DEFAULTS,
        config_file=config_file,
    )

    return generator, critic, refiner


def print_config_info() -> None:
    """設定の優先順位と環境変数名を表示"""
    print("""
設定の優先順位 (高い順):
    1. CLI引数 (--generator-model, --temperature, etc.)
    2. 環境変数
    3. 設定ファイル
    4. デフォルト値

設定ファイル:
    - --config PATH で明示指定
    - または CONFIG_FILE 環境変数
    - または自動探索: config.yaml / config.yml / config.json / .config.yaml / .config.yml / .config.json
    - --no-config で無効化

環境変数:
    [APIキー]
    GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY
    OPENAI_BASE_URL (OpenAIのbase_url)

    [モデルID]
    GEMINI_MODEL_ID / ANTHROPIC_MODEL_ID / OPENAI_CHAT_MODEL_ID

    [Generator (初期案作成)]
    REFLECTION_GENERATOR_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_GENERATOR_MODEL     : モデルID
    REFLECTION_GENERATOR_API_KEY   : APIキー (または GEMINI_API_KEY)
    REFLECTION_GENERATOR_BASE_URL  : base_url (主にOpenAI向け)
    REFLECTION_GENERATOR_TEMPERATURE: 温度

    [Critic (批評・改善提案)]
    REFLECTION_CRITIC_PROVIDER   : プロバイダー (gemini/anthropic/openai)
    REFLECTION_CRITIC_MODEL      : モデルID
    REFLECTION_CRITIC_API_KEY    : APIキー (または ANTHROPIC_API_KEY)
    REFLECTION_CRITIC_BASE_URL   : base_url (主にOpenAI向け)
    REFLECTION_CRITIC_TEMPERATURE : 温度

    [Refiner (最終版作成)]
    REFLECTION_REFINER_PROVIDER  : プロバイダー (gemini/anthropic/openai)
    REFLECTION_REFINER_MODEL     : モデルID
    REFLECTION_REFINER_API_KEY   : APIキー (または OPENAI_API_KEY)
    REFLECTION_REFINER_BASE_URL  : base_url (または OPENAI_BASE_URL)
    REFLECTION_REFINER_TEMPERATURE: 温度

    [共通パラメータ（全ロールに適用。ロール別より低優先）]
    REFLECTION_PROVIDER_STRATEGY: fixed / random / shuffle
    REFLECTION_PROVIDER_MODE     : fixed / random / shuffle (alias)
    REFLECTION_RANDOM_PROVIDERS  : true/false
    REFLECTION_SHUFFLE_PROVIDERS : true/false
    REFLECTION_TEMPERATURE       : 温度 (または LLM_TEMPERATURE)
    REFLECTION_DEVUI_PORT        : DevUIポート (または DEVUI_PORT)

デフォルト値:
    Generator: gemini / gemini-3-pro-preview
    Critic:    anthropic / claude-opus-4-1-20250805
    Refiner:   openai / gpt-5.2
""")
