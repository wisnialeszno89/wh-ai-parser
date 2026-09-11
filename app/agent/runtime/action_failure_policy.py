from abc import ABC, abstractmethod

from app.agent.agent_action import (
    AgentAction,
)

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)


class ActionFailurePolicy(ABC):
    """
    Decides how the runtime should react when an action
    fails during controlled execution.

    The policy intentionally does not perform recovery.

    It only answers the semantic question:

        What should happen next?
    """

    @abstractmethod
    def decide(
        self,
        action: AgentAction,
        result: ExecutionLoopResult,
        context: ExecutionContext,
    ) -> ActionFailureDecision:
        """
        Decide how execution should continue after
        an action failure.
        """

        raise NotImplementedError
