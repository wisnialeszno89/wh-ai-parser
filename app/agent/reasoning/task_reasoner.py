from abc import ABC, abstractmethod

from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)

from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)


class TaskReasoner(ABC):
    """
    Pluggable reasoning contract for initial task planning.

    This is intentionally separate from PlanReasoner, which is
    reserved for recovery after a failed verification cycle.
    """

    @abstractmethod
    def reason(
        self,
        context: TaskPlanningContext,
    ) -> ReasoningProposal | None:
        """
        Produce a semantic task proposal or None when no safe
        initial plan can be generated.
        """

        raise NotImplementedError
