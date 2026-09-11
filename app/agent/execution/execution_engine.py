from app.agent.agent_action import AgentAction

from app.agent.execution.execution_result import (
    ExecutionResult,
)

from app.agent.execution.executor_registry import (
    ExecutorRegistry,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class ExecutionEngine:
    """
    Controlled execution layer.

    Converts semantic actions into calls to registered
    environment-specific executors.
    """

    def __init__(
        self,
        registry: ExecutorRegistry,
    ) -> None:
        self.registry = registry

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        executor = self.registry.resolve(
            action
        )

        if executor is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=(
                    "No executor available for action: "
                    f"{action.name}"
                ),
                requires_manual_review=True,
            )

        return executor.execute(
            action,
            context,
        )
