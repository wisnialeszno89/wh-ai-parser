from abc import ABC, abstractmethod

from app.agent.agent_action import AgentAction
from app.agent.execution.execution_result import (
    ExecutionResult,
)
from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class ActionExecutor(ABC):
    """
    Base interface for controlled action execution.

    Executors receive semantic actions and execution context.

    The context allows actions to share structured state without
    coupling the generic execution engine to a specific program.
    """

    @abstractmethod
    def supports(
        self,
        action: AgentAction,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        raise NotImplementedError
