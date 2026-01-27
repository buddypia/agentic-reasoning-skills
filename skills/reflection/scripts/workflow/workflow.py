"""リフレクションパターン ワークフロー - 逐次実行: Generator -> Critic -> Refiner。"""

from .engine import WorkflowBuilder, Executor, WorkflowContext, handler

from .config import AgentConfig
from .types import PromptPayload
from .generator import GeneratorExecutor
from .critic import CriticExecutor
from .refiner import RefinerExecutor


class PromptIngress(Executor):
    """ユーザープロンプトを受け取り、リフレクションフローを開始するエントリーポイント。"""

    def __init__(self):
        super().__init__(id="prompt_ingress")

    @handler
    async def handle_string(self, prompt: str, ctx: WorkflowContext[PromptPayload]) -> None:
        payload = PromptPayload(text=prompt)
        await ctx.send_message(payload)


def build_reflection_workflow(
    generator_config: AgentConfig,
    critic_config: AgentConfig,
    refiner_config: AgentConfig,
    name: str = "multi_llm_reflection",
):
    """
    リフレクションパターンワークフローを構築する。

    フロー:
        [ユーザープロンプト]
              |
              v
        [Generator] - 初期ドラフトを作成
              |
              v
        [Critic] - レビューと批評
              |
              v
        [Refiner] - 最終的に洗練されたバージョンを作成
              |
              v
        [ReflectionResult]
    """
    builder = WorkflowBuilder(name=name)

    ingress = PromptIngress()
    generator = GeneratorExecutor(generator_config)
    critic = CriticExecutor(critic_config)
    refiner = RefinerExecutor(refiner_config)

    builder.set_start_executor(ingress)
    builder.add_edge(ingress, generator)
    builder.add_edge(generator, critic)
    builder.add_edge(critic, refiner)

    return builder.build()
