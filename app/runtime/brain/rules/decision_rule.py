from __future__ import annotations

from abc import ABC, abstractmethod

from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision


class DecisionRule(ABC):
    """
    Base class for every decision rule.

    Rules are evaluated in order of priority.
    The first rule returning a Decision wins.
    """

    priority: int = 100

    @abstractmethod
    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:
        """
        Return a Decision if the rule matches,
        otherwise return None.
        """
        raise NotImplementedError