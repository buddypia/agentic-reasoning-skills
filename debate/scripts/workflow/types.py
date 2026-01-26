"""討論パターン 型定義。"""

from typing import Any, Optional, List

from pydantic import BaseModel, ConfigDict, Field


class PromptPayload(BaseModel):
    """討論ワークフローの初期ユーザープロンプト/トピック。"""

    model_config = ConfigDict(extra="forbid")

    text: str
    metadata: Optional[dict[str, Any]] = None


class ProponentOutput(BaseModel):
    """Proponentエージェントの出力（支持/肯定的な視点）。"""

    model_config = ConfigDict(extra="forbid")

    position: str = Field(..., description="支持立場の明確な声明")
    arguments: List[str] = Field(default_factory=list, description="支持論拠")
    evidence: List[str] = Field(default_factory=list, description="証拠と例")
    benefits: List[str] = Field(default_factory=list, description="期待される利益")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="立場への信頼度")


class OpponentOutput(BaseModel):
    """Opponentエージェントの出力（反対/批判的な視点）。"""

    model_config = ConfigDict(extra="forbid")

    position: str = Field(..., description="反対立場の明確な声明")
    counter_arguments: List[str] = Field(default_factory=list, description="反論")
    risks: List[str] = Field(default_factory=list, description="リスクと懸念")
    weaknesses: List[str] = Field(default_factory=list, description="提案の弱点")
    alternatives: List[str] = Field(default_factory=list, description="代替アプローチ")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="立場への信頼度")


class StageRawData(BaseModel):
    """単一のLLM呼び出しに対するサニタイズされた生リクエスト/レスポンスデータ。"""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(..., description="プロバイダ名（例: openai, anthropic, gemini）")
    model: str = Field(..., description="呼び出しに使用したモデルID")
    duration_sec: Optional[float] = Field(default=None, description="呼び出しの所要時間（秒）")

    # 入力（シークレットは含まない）
    system_prompt: Optional[str] = Field(default=None, description="呼び出しに使用したシステムプロンプト")
    user_prompt: Optional[str] = Field(default=None, description="呼び出しに使用したユーザー/コンテンツプロンプト")
    request: dict[str, Any] = Field(default_factory=dict, description="プロバイダリクエストペイロード（サニタイズ済み）")

    # 出力
    response_text: Optional[str] = Field(default=None, description="モデルが返した生テキスト")
    response_meta: dict[str, Any] = Field(default_factory=dict, description="使用量やIDなどのメタデータ（サニタイズ済み）")
    parsed_output: Optional[dict[str, Any]] = Field(default=None, description="パース/正規化された出力（サニタイズ済み）")
    error: Optional[str] = Field(default=None, description="エラーメッセージ（ある場合）")


class DebateRawData(BaseModel):
    """討論ワークフロー全体の生データ（Proponent/Opponent/Moderator）。"""

    model_config = ConfigDict(extra="forbid")

    proponent: Optional[StageRawData] = None
    opponent: Optional[StageRawData] = None
    moderator: Optional[StageRawData] = None


class ModeratorOutput(BaseModel):
    """Moderatorエージェントの出力（中立的な評価と最終判定）。"""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., description="双方の視点のサマリー")
    proponent_score: int = Field(5, ge=0, le=10, description="Proponentの論拠スコア")
    opponent_score: int = Field(5, ge=0, le=10, description="Opponentの論拠スコア")
    key_insights: List[str] = Field(default_factory=list, description="討論からの重要な洞察")
    final_verdict: str = Field(..., description="最終的なバランスの取れた判定")
    recommendation: str = Field(..., description="実行可能な推奨事項")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="判定への信頼度")


class DebateResult(BaseModel):
    """完全な討論ワークフロー結果。"""

    model_config = ConfigDict(extra="forbid")

    original_topic: str = Field(..., description="元の討論トピック")

    # Proponentステージ
    proponent_position: str = Field(..., description="Proponentの立場")
    proponent_arguments: List[str] = Field(default_factory=list)
    proponent_evidence: List[str] = Field(default_factory=list)
    proponent_benefits: List[str] = Field(default_factory=list)
    proponent_confidence: float = Field(0.7)

    # Opponentステージ
    opponent_position: str = Field(..., description="Opponentの立場")
    opponent_counter_arguments: List[str] = Field(default_factory=list)
    opponent_risks: List[str] = Field(default_factory=list)
    opponent_weaknesses: List[str] = Field(default_factory=list)
    opponent_alternatives: List[str] = Field(default_factory=list)
    opponent_confidence: float = Field(0.7)

    # Moderatorステージ
    debate_summary: str = Field(..., description="Moderatorのサマリー")
    proponent_score: int = Field(5, description="Proponentのスコア")
    opponent_score: int = Field(5, description="Opponentのスコア")
    key_insights: List[str] = Field(default_factory=list)
    final_verdict: str = Field(..., description="最終判定")
    recommendation: str = Field(..., description="最終推奨事項")

    # メタデータ
    total_duration_sec: float = Field(0.0)
    proponent_model: str = Field("")
    opponent_model: str = Field("")
    moderator_model: str = Field("")

    # 生トレース（オプション）
    raw: Optional[DebateRawData] = Field(
        default=None,
        description="各LLMステージのサニタイズされた生リクエスト/レスポンスデータ（デバッグ用）",
    )


# 構造化出力用のJSONスキーマ
PROPONENT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "position": {
            "type": "string",
            "description": "支持立場の明確な声明",
        },
        "arguments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "立場を支持する論拠",
        },
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "description": "立場を支持する証拠と例",
        },
        "benefits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "立場の期待される利益",
        },
        "confidence": {
            "type": "number",
            "description": "信頼度レベル 0-1",
        },
    },
    "required": ["position", "arguments", "evidence", "benefits", "confidence"],
    "additionalProperties": False,
}

OPPONENT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "position": {
            "type": "string",
            "description": "反対立場の明確な声明",
        },
        "counter_arguments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "提案に対する反論",
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "リスクと懸念",
        },
        "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "元の提案の弱点",
        },
        "alternatives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "検討すべき代替アプローチ",
        },
        "confidence": {
            "type": "number",
            "description": "信頼度レベル 0-1",
        },
    },
    "required": ["position", "counter_arguments", "risks", "weaknesses", "alternatives", "confidence"],
    "additionalProperties": False,
}

MODERATOR_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "双方の視点のサマリー",
        },
        "proponent_score": {
            "type": "integer",
            "description": "Proponentの論拠スコア (0-10)",
        },
        "opponent_score": {
            "type": "integer",
            "description": "Opponentの論拠スコア (0-10)",
        },
        "key_insights": {
            "type": "array",
            "items": {"type": "string"},
            "description": "討論からの重要な洞察",
        },
        "final_verdict": {
            "type": "string",
            "description": "最終的なバランスの取れた判定",
        },
        "recommendation": {
            "type": "string",
            "description": "実行可能な推奨事項",
        },
        "confidence": {
            "type": "number",
            "description": "信頼度レベル 0-1",
        },
    },
    "required": ["summary", "proponent_score", "opponent_score", "key_insights", "final_verdict", "recommendation", "confidence"],
    "additionalProperties": False,
}
