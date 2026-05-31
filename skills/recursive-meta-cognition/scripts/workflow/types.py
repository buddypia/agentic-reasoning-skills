"""リフレクションパターン 型定義（5段階: 分解→解決→検証→統合→反省）。"""

from typing import Any, Optional, List

from pydantic import BaseModel, ConfigDict, Field


class PromptPayload(BaseModel):
    """リフレクションワークフローの初期ユーザープロンプト。"""

    model_config = ConfigDict(extra="forbid")

    text: str
    metadata: Optional[dict[str, Any]] = None


class DecompositionOutput(BaseModel):
    """分解ステージの出力。"""

    model_config = ConfigDict(extra="forbid")

    subtasks: List[str] = Field(default_factory=list, description="課題を分解したサブタスク")
    assumptions: List[str] = Field(default_factory=list, description="前提・仮定")
    constraints: List[str] = Field(default_factory=list, description="制約条件")
    questions: List[str] = Field(default_factory=list, description="不足情報や確認事項")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="分解の確信度")


class SolutionItem(BaseModel):
    """サブタスクごとの解決案。"""

    model_config = ConfigDict(extra="forbid")

    subtask: str = Field(..., description="対象サブタスク")
    answer: str = Field(..., description="サブタスクに対する解決案")


class SolutionOutput(BaseModel):
    """解決ステージの出力。"""

    model_config = ConfigDict(extra="forbid")

    solutions: List[SolutionItem] = Field(default_factory=list, description="サブタスク別の解決案")
    open_questions: List[str] = Field(default_factory=list, description="未解決・要確認事項")
    risks: List[str] = Field(default_factory=list, description="潜在的リスクや注意点")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="解決の確信度")


class VerificationOutput(BaseModel):
    """検証ステージの出力。"""

    model_config = ConfigDict(extra="forbid")

    issues: List[str] = Field(default_factory=list, description="論理的矛盾・誤り・飛躍")
    corrections: List[str] = Field(default_factory=list, description="修正案")
    self_corrections: List[str] = Field(default_factory=list, description="自律修正の記録")
    validation_notes: List[str] = Field(default_factory=list, description="追加の検証コメント")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="検証の確信度")


class IntegrationOutput(BaseModel):
    """統合ステージの出力。"""

    model_config = ConfigDict(extra="forbid")

    integrated_answer: str = Field(..., description="統合された回答草案")
    applied_corrections: List[str] = Field(default_factory=list, description="反映した修正点")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="統合の確信度")


class ReflectionOutput(BaseModel):
    """反省ステージの出力（最終回答）。"""

    model_config = ConfigDict(extra="forbid")

    final_response: str = Field(..., description="最終回答（確信度・不確実性・自律修正を含む）")
    confidence_score: float = Field(0.7, ge=0.0, le=1.0, description="最終回答の確信度")
    uncertainties: List[str] = Field(default_factory=list, description="不確実性が残る点")
    self_corrections: List[str] = Field(default_factory=list, description="自律修正の記録")
    reflection_notes: List[str] = Field(default_factory=list, description="死角や別視点に関する反省")


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
    """リフレクションワークフロー全体の生データ（5段階）。"""

    model_config = ConfigDict(extra="forbid")

    decomposer: Optional[StageRawData] = None
    solver: Optional[StageRawData] = None
    verifier: Optional[StageRawData] = None
    integrator: Optional[StageRawData] = None
    reflector: Optional[StageRawData] = None


class ReflectionResult(BaseModel):
    """完全なリフレクションワークフロー結果。"""

    model_config = ConfigDict(extra="forbid")

    original_prompt: str = Field(..., description="元のユーザープロンプト")

    decomposition: DecompositionOutput
    solution: SolutionOutput
    verification: VerificationOutput
    integration: IntegrationOutput
    reflection: ReflectionOutput

    # メタデータ
    total_duration_sec: float = Field(0.0)
    decomposer_model: str = Field("")
    solver_model: str = Field("")
    verifier_model: str = Field("")
    integrator_model: str = Field("")
    reflector_model: str = Field("")

    # 生トレース（オプション）
    raw: Optional[ReflectionRawData] = Field(
        default=None,
        description="各LLMステージのサニタイズされた生リクエスト/レスポンスデータ（デバッグ用）",
    )


# 構造化出力用のJSONスキーマ
DECOMPOSITION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "subtasks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "課題を分解したサブタスク",
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "前提・仮定",
        },
        "constraints": {
            "type": "array",
            "items": {"type": "string"},
            "description": "制約条件",
        },
        "questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "不足情報や確認事項",
        },
        "confidence": {
            "type": "number",
            "description": "分解の確信度 0-1",
        },
    },
    "required": ["subtasks", "assumptions", "constraints", "questions", "confidence"],
    "additionalProperties": False,
}

SOLUTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "solutions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subtask": {"type": "string"},
                    "answer": {"type": "string"},
                },
                "required": ["subtask", "answer"],
                "additionalProperties": False,
            },
            "description": "サブタスク別の解決案",
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "未解決・要確認事項",
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "潜在的リスクや注意点",
        },
        "confidence": {
            "type": "number",
            "description": "解決の確信度 0-1",
        },
    },
    "required": ["solutions", "open_questions", "risks", "confidence"],
    "additionalProperties": False,
}

VERIFICATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "論理的矛盾・誤り・飛躍",
        },
        "corrections": {
            "type": "array",
            "items": {"type": "string"},
            "description": "修正案",
        },
        "self_corrections": {
            "type": "array",
            "items": {"type": "string"},
            "description": "自律修正の記録",
        },
        "validation_notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "追加の検証コメント",
        },
        "confidence": {
            "type": "number",
            "description": "検証の確信度 0-1",
        },
    },
    "required": ["issues", "corrections", "self_corrections", "validation_notes", "confidence"],
    "additionalProperties": False,
}

INTEGRATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "integrated_answer": {
            "type": "string",
            "description": "統合された回答草案",
        },
        "applied_corrections": {
            "type": "array",
            "items": {"type": "string"},
            "description": "反映した修正点",
        },
        "confidence": {
            "type": "number",
            "description": "統合の確信度 0-1",
        },
    },
    "required": ["integrated_answer", "applied_corrections", "confidence"],
    "additionalProperties": False,
}

REFLECTION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "final_response": {
            "type": "string",
            "description": "最終回答（確信度・不確実性・自律修正を含む）",
        },
        "confidence_score": {
            "type": "number",
            "description": "最終回答の確信度 0-1",
        },
        "uncertainties": {
            "type": "array",
            "items": {"type": "string"},
            "description": "不確実性が残る点",
        },
        "self_corrections": {
            "type": "array",
            "items": {"type": "string"},
            "description": "自律修正の記録",
        },
        "reflection_notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "死角や別視点に関する反省",
        },
    },
    "required": [
        "final_response",
        "confidence_score",
        "uncertainties",
        "self_corrections",
        "reflection_notes",
    ],
    "additionalProperties": False,
}
