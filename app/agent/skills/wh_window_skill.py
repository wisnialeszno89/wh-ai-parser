from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
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
        intent = AgentPlanner().detect_intent(
            request
        )

        if intent == AgentIntent.CREATE_QUOTE:
            return self._plan_create_quote()

        return AgentPlanner().plan(
            request
        )

    @staticmethod
    def _plan_create_quote() -> ActionPlan:
        return ActionPlan(
            intent=AgentIntent.CREATE_QUOTE,
            confidence=1.0,
            requires_manual_review=False,
            steps=(
                ActionStep(
                    index=1,
                    action=AgentAction(
                        name="analyze_request",
                        description=(
                            "Analyze salesman request "
                            "and extract quotation intent."
                        ),
                    ),
                ),
                ActionStep(
                    index=2,
                    action=AgentAction(
                        name="collect_offer_context",
                        description=(
                            "Collect technical, dimensional "
                            "and commercial offer context."
                        ),
                    ),
                ),
                ActionStep(
                    index=3,
                    action=AgentAction(
                        name="validate_offer",
                        description=(
                            "Validate collected offer context "
                            "and detect missing or conflicting data."
                        ),
                    ),
                ),
                ActionStep(
                    index=4,
                    action=AgentAction(
                        name="build_construction",
                        description=(
                            "Build or select the appropriate "
                            "window construction based on the "
                            "validated offer context."
                        ),
                    ),
                ),
                ActionStep(
                    index=5,
                    action=AgentAction(
                        name="prepare_quote",
                        description=(
                            "Prepare quotation workflow "
                            "for controlled execution."
                        ),
                        requires_confirmation=True,
                    ),
                ),
            ),
        )
