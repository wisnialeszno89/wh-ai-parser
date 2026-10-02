from abc import ABC, abstractmethod

from app.agent.reasoning.replanning_context import (
    ReplanningContext,
)

from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)


class PlanReasoner(ABC):
    """
    Pluggable reasoning contract used to recover from
    failed verification.

    Implementations may use:
    - an LLM
    - a local model
    - a deterministic planner
    - a future hybrid reasoner

    The implementation returns semantic actions only.
    """

    @abstractmethod
    def reason(
        self,
        context: ReplanningContext,
    ) -> ReasoningProposal | None:
        """
        Produce a semantic recovery proposal or None when
        no safe alternative can be generated.
        """

        raise NotImplementedError
