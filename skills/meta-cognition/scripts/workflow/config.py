"""メタ認知パターン エージェント設定。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """メタ認知パターンエージェントの設定。"""

    name: str
    role: str  # "decomposer", "solver", "verifier", "integrator", "reflector"
    provider: str  # "openai", "anthropic", "gemini"
    model: str
    api_key: Optional[str]
    base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    timeout_sec: float = 120.0
    enabled: bool = True

    def normalized_provider(self) -> str:
        return self.provider.strip().lower()
