from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.skills.agent_skill import AgentSkill


class ExcelSkill(AgentSkill):
    """
    Placeholder for spreadsheet workflows.

    The architecture exists now so Excel can later gain:
    - workbook inspection
    - spreadsheet reasoning
    - data extraction
    - formula operations
    - controlled application execution
    """

    @property
    def capability_name(self) -> str:
        return "EXCEL"

    def supports(
        self,
        intent: AgentIntent,
    ) -> bool:
        return False

    def plan(
        self,
        request: AgentRequest,
    ) -> ActionPlan:
        raise NotImplementedError(
            "Excel workflows are not implemented yet."
        )
