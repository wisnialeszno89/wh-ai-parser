from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.skills.agent_skill import AgentSkill


class WordSkill(AgentSkill):
    """
    Initial skill for document and customer communication.

    Real document generation and application control
    will be connected later.
    """

    @property
    def capability_name(self) -> str:
        return "WORD"

    def supports(
        self,
        intent: AgentIntent,
    ) -> bool:
        return intent == (
            AgentIntent.WRITE_CUSTOMER_REPLY
        )

    def plan(
        self,
        request: AgentRequest,
    ) -> ActionPlan:
        raise NotImplementedError(
            "Word workflows are not implemented yet."
        )
