from app.agent.agent_request import AgentRequest
from app.agent.agent_response import AgentResponse
from app.agent.planning.agent_planner import AgentPlanner


class Agent:
    """
    High-level application agent.

    Independent from UI, browser, CAD or LLM implementation.
    Future integrations such as Navimind can use this class
    as the central application entry point.
    """

    def __init__(
        self,
        planner: AgentPlanner | None = None,
    ) -> None:

        self.planner = (
            planner
            if planner is not None
            else AgentPlanner()
        )

    def handle(
        self,
        request: AgentRequest,
    ) -> AgentResponse:

        plan = self.planner.plan(request)

        if plan.intent.value == "unknown":

            message = (
                "Nie jestem jeszcze pewien, "
                "co dokładnie chcesz zrobić. "
                "Doprecyzuj proszę zadanie."
            )

        else:

            message = (
                "Rozpoznałem zadanie: "
                f"{plan.intent.value}. "
                "Przygotowałem plan działania."
            )

        return AgentResponse(
            intent=plan.intent,
            message=message,
            actions=tuple(
                step.action
                for step in plan.steps
            ),
            requires_manual_review=(
                plan.requires_manual_review
            ),
            confidence=plan.confidence,
        )
