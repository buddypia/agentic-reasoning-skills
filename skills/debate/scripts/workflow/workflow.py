"""討論パターン ワークフロー - 逐次実行: Proponent -> Opponent -> Moderator。"""

from .engine import WorkflowBuilder, Executor, WorkflowContext, handler

from .config import AgentConfig
from .types import PromptPayload, DebateResult
from .proponent import ProponentExecutor
from .opponent import OpponentExecutor
from .moderator import ModeratorExecutor


class PromptIngress(Executor):
    """ユーザーの討論テーマを受け取り、討論フローを開始するエントリーポイント。"""

    def __init__(self):
        super().__init__(id="prompt_ingress")

    @handler
    async def handle_string(self, topic: str, ctx: WorkflowContext[PromptPayload]) -> None:
        payload = PromptPayload(text=topic)
        await ctx.send_message(payload)


def build_debate_workflow(
    proponent_config: AgentConfig,
    opponent_config: AgentConfig,
    moderator_config: AgentConfig,
    name: str = "multi_llm_debate",
):
    """
    討論パターンワークフローを構築する。

    フロー:
        [ユーザーの討論テーマ]
              |
              v
        [Proponent (賛成派)] - 支持/肯定的な観点で分析
              |
              v
        [Opponent (反対派)] - 批判/反対の観点で分析
              |
              v
        [Moderator (中立派)] - 両者を評価し最終判断を提示
              |
              v
        [DebateResult]

    引数:
        proponent_config: Proponentエージェントの設定
        opponent_config: Opponentエージェントの設定
        moderator_config: Moderatorエージェントの設定
        name: ワークフローの名前

    戻り値:
        設定済みのワークフローインスタンス
    """
    builder = WorkflowBuilder(name=name)

    # エグゼキュータを作成
    ingress = PromptIngress()
    proponent = ProponentExecutor(proponent_config)
    opponent = OpponentExecutor(opponent_config)
    moderator = ModeratorExecutor(moderator_config)

    # 逐次フローをセットアップ
    builder.set_start_executor(ingress)
    builder.add_edge(ingress, proponent)
    builder.add_edge(proponent, opponent)
    builder.add_edge(opponent, moderator)

    return builder.build()
