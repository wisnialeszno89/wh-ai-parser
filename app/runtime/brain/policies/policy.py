from abc import ABC
from abc import abstractmethod

from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision


class Policy(ABC):
    """
    Base contract for every runtime policy.
    """

    #
    # Lower value = higher priority.
    #
    priority: int = 100

    @property
    def name(
        self,
    ) -> str:

        return self.__class__.__name__

    @abstractmethod
    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:
        """
        Return a Decision to interrupt the normal execution flow.

        Return None to allow evaluation of the next policy.
        """
        raise NotImplementedError