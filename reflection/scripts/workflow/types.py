"""リフレクションパターン 型定義。"""

from typing import Any, Optional, List

from pydantic import BaseModel, ConfigDict, Field


class PromptPayload(BaseModel):
    """リフレクションワークフローの初期ユーザープロンプト。"""

    model_config = ConfigDict(extra="forbid")

    text: str
    metadata: Optional[dict[str, Any]] = None


class GeneratorOutput(BaseModel):
    """Generatorエージェントの出力（初期ドラフト）。"""

    model_config = ConfigDict(extra="forbid")

    draft: str = Field(..., description="Generatorが作成した初期ドラフト")
    key_points: List[str] = Field(default_factory=list, description="カバーしたキーポイント")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="信頼度レベル")


class CriticOutput(BaseModel):
    """Criticエージェントの出力（フィードバックと改善点）。"""

    model_config = ConfigDict(extra="forbid")

    strengths: List[str] = Field(default_factory=list, description="ドラフトの長所")
    weaknesses: List[str] = Field(default_factory=list, description="改善すべき弱点")
    suggestions: List[str] = Field(default_factory=list, description="具体的な改善提案")
    overall_score: int = Field(5, ge=0, le=10, description="総合品質スコア 0-10")
    critical_issues: List[str] = Field(default_factory=list, description="必ず修正すべき重大な問題")


class RefinerOutput(BaseModel):
    """Refinerエージェントの出力（最終版）。"""

    model_config = ConfigDict(extra="forbid")

    final_content: str = Field(..., description="最終的に洗練されたコンテンツ")
    improvements_made: List[str] = Field(default_factory=list, description="適用した改善点のリスト")
    quality_score: int = Field(8, ge=0, le=10, description="最終品質スコア")


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


class ReflectionRawData(BaseModel):
    """リフレクションワークフロー全体の生データ（Generator/Critic/Refiner）。"""

    model_config = ConfigDict(extra="forbid")

    generator: Optional[StageRawData] = None
    critic: Optional[StageRawData] = None
    refiner: Optional[StageRawData] = None


class ReflectionResult(BaseModel):
    """完全なリフレクションワークフロー結果。"""

    model_config = ConfigDict(extra="forbid")

    original_prompt: str = Field(..., description="元のユーザープロンプト")

    # Generatorステージ
    initial_draft: str = Field(..., description="Generatorからの初期ドラフト")
    generator_confidence: float = Field(0.7, description="Generatorの信頼度")

    # Criticステージ
    critic_strengths: List[str] = Field(default_factory=list)
    critic_weaknesses: List[str] = Field(default_factory=list)
    critic_suggestions: List[str] = Field(default_factory=list)
    critic_score: int = Field(5, description="初期ドラフトに対するCriticのスコア")

    # Refinerステージ
    final_content: str = Field(..., description="最終的に洗練されたコンテンツ")
    improvements_made: List[str] = Field(default_factory=list)
    final_score: int = Field(8, description="最終品質スコア")

    # メタデータ
    total_duration_sec: float = Field(0.0)
    generator_model: str = Field("")
    critic_model: str = Field("")
    refiner_model: str = Field("")

    # 生トレース（オプション）
    raw: Optional[ReflectionRawData] = Field(
        default=None,
        description="各LLMステージのサニタイズされた生リクエスト/レスポンスデータ（デバッグ用）",
    )


# 構造化出力用のJSONスキーマ
GENERATOR_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "draft": {
            "type": "string",
            "description": "初期ドラフトコンテンツ",
        },
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "ドラフトでカバーしたキーポイント",
        },
        "confidence": {
            "type": "number",
            "description": "信頼度レベル 0-1",
        },
    },
    "required": ["draft", "key_points", "confidence"],
    "additionalProperties": False,
}

CRITIC_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "ドラフトの長所",
        },
        "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "改善すべき弱点",
        },
        "suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "具体的な改善提案",
        },
        "overall_score": {
            "type": "integer",
            "description": "総合品質スコア 0-10",
        },
        "critical_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "必ず修正すべき重大な問題",
        },
    },
    "required": ["strengths", "weaknesses", "suggestions", "overall_score", "critical_issues"],
    "additionalProperties": False,
}

REFINER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "final_content": {
            "type": "string",
            "description": "最終的に洗練されたコンテンツ",
        },
        "improvements_made": {
            "type": "array",
            "items": {"type": "string"},
            "description": "適用した改善点のリスト",
        },
        "quality_score": {
            "type": "integer",
            "description": "最終品質スコア 0-10",
        },
    },
    "required": ["final_content", "improvements_made", "quality_score"],
    "additionalProperties": False,
}
