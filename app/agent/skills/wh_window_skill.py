from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.agent_planner import AgentPlanner
from app.agent.skills.agent_skill import AgentSkill


class WHWindowSkill(AgentSkill):
    """
    Specialized skill for window quotation workflows.

    This skill currently delegates planning to the existing
    AgentPlanner so the current quotation behavior remains
    unchanged.

    Later this skill will connect directly to:
    - OfferContext
    - DecisionEngine
    - construction catalog
    - quote orchestration
    - controlled WH execution
    """

    @property
    def capability_name(self) -> str:
        return "WH_WINDOW"

    def supports(
        self,
        intent: AgentIntent,
    ) -> bool:
        return intent in {
            AgentIntent.CREATE_QUOTE,
            AgentIntent.MODIFY_QUOTE,
            AgentIntent.CHECK_TECHNICAL,
            AgentIntent.COMPARE_VARIANTS,
            AgentIntent.EXECUTE_IN_WH,
            AgentIntent.OBSERVE_WORKFLOW,
        }

    def plan(
        self,
        request: AgentRequest,
    ) -> ActionPlan:
        return AgentPlanner().plan(
            request
        )
