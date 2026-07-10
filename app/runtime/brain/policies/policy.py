from abc import ABC
from abc import abstractmethod

from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision


class Policy(ABC):

    @abstractmethod
    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:

        pass