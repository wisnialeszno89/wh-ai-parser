import json

from app.agent.adapters.browser_adapter import (
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_request import AgentRequest
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)
from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)
from app.agent.reasoning.reasoning_task_planner import (
    ReasoningTaskPlanner,
)
from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)
from app.agent.reasoning.task_reasoner import TaskReasoner


class Response:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def create_browser_page():
    return BrowserPage(
        url="https://example.com/form",
        title="Example Form",
        text="Zamówienie klienta",
        elements=(
            BrowserElement(
                label="Imię",
                kind="textbox",
                interaction_capability="EDITABLE",
                current_value="",
                confidence=0.99,
                metadata={
                    "provider": "playwright",
                    "strategy": "label",
                    "locator_value": "Imię",
                    "role": "textbox",
                },
            ),
            BrowserElement(
                label="Dalej",
                kind="button",
                interaction_capability="CLICKABLE",
                confidence=0.98,
                metadata={
                    "provider": "playwright",
                    "strategy": "text",
                    "locator_value": "Dalej",
                    "role": "button",
                },
            ),
        ),
    )


def test_navimind_reasoner_sends_browser_world_semantically():
    captured = {}

    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body

        return Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Enter the requested name.",
                "confidence": 0.97,
                "action": {
                    "name": "browser_write_text",
                    "description": "Enter the customer name.",
                    "target": "Imię",
                    "value": "Adam",
                },
                "requires_manual_review": False,
            }
        )

    context = TaskPlanningContext(
        request_message="Wpisz imię klienta Adam",
        intent="computer_use",
        session_id="browser-session",
        browser_page=create_browser_page(),
    )

    proposal = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    ).reason(context)

    assert proposal is not None
    assert proposal.actions[0].name == "browser_write_text"

    world = captured["body"]["world"]
    assert world["active_application"] == "Browser"
    assert world["active_window_title"] == "Example Form"
    assert world["visible_elements"][0]["label"] == "Imię"
    assert world["visible_elements"][0]["interaction_capability"] == "editable"
    assert world["metadata"]["browser_url"] == (
        "https://example.com/form"
    )
    assert world["metadata"]["browser_text"] == "Zamówienie klienta"

    serialized = json.dumps(captured["body"])
    assert "provider" not in serialized
    assert "locator_value" not in serialized
    assert "strategy" not in serialized
    assert "runtime_id" not in serialized


def test_reasoning_planner_accepts_browser_target_from_browser_world():
    class BrowserReasoner(TaskReasoner):
        def reason(self, context):
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_click",
                        description="Click the visible next control.",
                        target="Dalej",
                    ),
                ),
                rationale="Advance the browser workflow.",
                confidence=0.95,
            )

    context = TaskPlanningContext(
        request_message="Przejdź dalej",
        intent="computer_use",
        browser_page=create_browser_page(),
        world=__import__(
            "app.agent.bridge.world_state",
            fromlist=["WorldState"],
        ).WorldState.from_browser_page(
            create_browser_page()
        ),
    )

    plan = ReasoningTaskPlanner(BrowserReasoner()).plan(
        context=context
    )

    assert plan is not None
    assert plan.steps[0].action.name == "browser_click"
    assert plan.steps[0].action.target == "Dalej"
    assert plan.steps[0].action.requires_environment_observation is False


def test_reasoning_planner_rejects_browser_action_without_browser_context():
    class BrowserReasoner(TaskReasoner):
        def reason(self, context):
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_click",
                        description="Click the control.",
                        target="Dalej",
                    ),
                ),
                rationale="Browser action without browser context.",
                confidence=0.95,
            )

    planner = ReasoningTaskPlanner(BrowserReasoner())

    context = TaskPlanningContext(
        request_message="Przejdź dalej",
        intent="computer_use",
    )

    assert planner.plan(context=context) is None
    assert planner.last_failure_reason == "browser_context_missing"


def test_browser_task_context_payload_does_not_embed_provider_metadata():
    page = create_browser_page()

    context = TaskPlanningContext(
        request_message="Przeczytaj stronę",
        intent="computer_use",
        browser_page=page,
        world=__import__(
            "app.agent.bridge.world_state",
            fromlist=["WorldState"],
        ).WorldState.from_browser_page(page),
    )

    payload = context.to_payload()
    serialized = json.dumps(payload)

    assert "provider" not in serialized
    assert "locator_value" not in serialized
    assert "strategy" not in serialized
