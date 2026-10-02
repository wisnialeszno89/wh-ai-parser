from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.skills.agent_skill import AgentSkill


class ComputerUseSkill(AgentSkill):
    """
    Generic computer-use skill used when no domain-specific intent is known.

    Autonomous reasoning supplies the semantic action plan. The skill itself
    remains a safe fallback and never invents application-specific workflows.
    """

    @property
    def capability_name(self) -> str:
        return "COMPUTER_USE"

    def supports(self, intent: AgentIntent) -> bool:
        return intent == AgentIntent.COMPUTER_USE

    def plan(self, request: AgentRequest) -> ActionPlan:
        return ActionPlan(
            intent=AgentIntent.COMPUTER_USE,
            steps=(),
            confidence=0.0,
            requires_manual_review=True,
        )
