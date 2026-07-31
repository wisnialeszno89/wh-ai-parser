from abc import ABC, abstractmethod

from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision


class BasePolicy(ABC):
    """
    Base class for every runtime policy.
    """

    #
    # Lower value = higher priority.
    #

    priority: int = 100

    @abstractmethod
    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:
        """
        Return Decision when policy wants
        to interrupt normal execution.

        Return None when execution should continue.
        """
        raise NotImplementedError