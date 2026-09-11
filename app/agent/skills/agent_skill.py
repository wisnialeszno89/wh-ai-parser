from abc import ABC, abstractmethod

from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan


class AgentSkill(ABC):
    """
    Base contract for a specialized agent skill.

    A skill owns domain-specific knowledge and planning logic.

    Skills do not directly perform uncontrolled GUI actions.
    Execution remains a separate controlled layer.
    """

    @property
    @abstractmethod
    def capability_name(self) -> str:
        """
        Capability handled by this skill.
        """
        raise NotImplementedError

    @abstractmethod
    def supports(
        self,
        intent: AgentIntent,
    ) -> bool:
        """
        Return whether this skill supports the intent.
        """
        raise NotImplementedError

    @abstractmethod
    def plan(
        self,
        request: AgentRequest,
    ) -> ActionPlan:
        """
        Create a domain-specific action plan.
        """
        raise NotImplementedError
