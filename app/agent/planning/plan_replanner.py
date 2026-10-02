from abc import ABC, abstractmethod

from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.execution_context import (
    ExecutionContext,
)
from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)


class PlanReplanner(ABC):
    """
    Produces a replacement action plan after a failed
    verification cycle.

    The replanner reasons about what should happen next.
    It does not execute actions.

    This keeps replanning inside the planning layer while
    AgentControlLoop remains responsible for controlled
    execution.
    """

    @abstractmethod
    def replan(
        self,
        *,
        plan: ActionPlan,
        failed_step: ActionStep,
        execution_result: ExecutionLoopResult,
        context: ExecutionContext,
    ) -> ActionPlan | None:
        """
        Return a replacement continuation or None when
        no safe alternative plan can be produced.
        """

        raise NotImplementedError
