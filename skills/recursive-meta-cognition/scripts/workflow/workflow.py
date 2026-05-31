"""リフレクションパターン ワークフロー - 逐次実行: 分解→解決→検証→統合→反省。"""

from .engine import WorkflowBuilder, Executor, WorkflowContext, handler

from .config import AgentConfig
from .types import PromptPayload
from .decomposer import DecomposerExecutor
from .solver import SolverExecutor
from .verifier import VerifierExecutor
from .integrator import IntegratorExecutor
from .reflector import ReflectorExecutor


class PromptIngress(Executor):
    """ユーザープロンプトを受け取り、リフレクションフローを開始するエントリーポイント。"""

    def __init__(self):
        super().__init__(id="prompt_ingress")

    @handler
    async def handle_string(self, prompt: str, ctx: WorkflowContext[PromptPayload]) -> None:
        payload = PromptPayload(text=prompt)
        await ctx.send_message(payload)


def build_reflection_workflow(
    decomposer_config: AgentConfig,
    solver_config: AgentConfig,
    verifier_config: AgentConfig,
    integrator_config: AgentConfig,
    reflector_config: AgentConfig,
    name: str = "multi_llm_reflection",
):
    """
    リフレクションパターンワークフローを構築する。

    フロー:
        [ユーザープロンプト]
              |
              v
        [Decomposer] - 課題を分解
              |
              v
        [Solver] - サブタスクを解決
              |
              v
        [Verifier] - 解決案の検証と自律修正
              |
              v
        [Integrator] - 統合された回答草案を作成
              |
              v
        [Reflector] - 反省と確信度を付与し最終回答
              |
              v
        [ReflectionResult]
    """
    builder = WorkflowBuilder(name=name)

    ingress = PromptIngress()
    decomposer = DecomposerExecutor(decomposer_config)
    solver = SolverExecutor(solver_config)
    verifier = VerifierExecutor(verifier_config)
    integrator = IntegratorExecutor(integrator_config)
    reflector = ReflectorExecutor(reflector_config)

    builder.set_start_executor(ingress)
    builder.add_edge(ingress, decomposer)
    builder.add_edge(decomposer, solver)
    builder.add_edge(solver, verifier)
    builder.add_edge(verifier, integrator)
    builder.add_edge(integrator, reflector)

    return builder.build()
