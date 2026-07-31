from abc import ABC, abstractmethod

from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision


class DecisionRule(ABC):

    priority: int = 100

    @abstractmethod
    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:
        """
        Return a Decision if this rule applies.

        Return None if the next rule should be evaluated.
        """
        raise NotImplementedError