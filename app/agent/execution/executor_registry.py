from app.agent.agent_action import AgentAction
from app.agent.execution.action_executor import (
    ActionExecutor,
)


class ExecutorRegistry:
    """
    Registry of available action executors.

    The registry selects the first executor that explicitly
    supports a semantic action.
    """

    def __init__(
        self,
        executors: tuple[ActionExecutor, ...] = (),
    ) -> None:
        self._executors = list(executors)

    def register(
        self,
        executor: ActionExecutor,
    ) -> None:
        self._executors.append(executor)

    def resolve(
        self,
        action: AgentAction,
    ) -> ActionExecutor | None:

        for executor in self._executors:
            if executor.supports(action):
                return executor

        return None

    def all(
        self,
    ) -> tuple[ActionExecutor, ...]:
        return tuple(self._executors)
