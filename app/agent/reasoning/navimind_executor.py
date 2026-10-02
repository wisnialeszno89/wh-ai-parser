from app.agent.agent_action import AgentAction
from app.agent.execution.action_executor import (
    ActionExecutor,
)
from app.agent.execution.execution_result import (
    ExecutionResult,
)
from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class NaviMindSemanticActionExecutor(ActionExecutor):
    """
    Safe default adapter for NaviMind semantic actions.

    It deliberately executes only actions explicitly registered by
    the local runtime. Unknown remote actions are rejected instead
    of being guessed or translated into low-level input.
    """

    SUPPORTED_ACTIONS = {
        "analyze_request",
        "collect_offer_context",
        "validate_offer",
        "build_construction",
        "prepare_quote",
    }

    def supports(
        self,
        action: AgentAction,
    ) -> bool:
        return action.name in self.SUPPORTED_ACTIONS

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        # Reuse the existing WH semantic executor without
        # exposing its implementation to NaviMind.
        from app.agent.execution.wh_action_executor import (
            WHActionExecutor,
        )

        return WHActionExecutor().execute(
            action,
            context,
        )
