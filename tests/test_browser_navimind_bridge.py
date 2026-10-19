import json

from app.agent.adapters.browser_adapter import (
    BrowserElement,
    BrowserPage,
)
from app.agent.bridge.world_state import WorldState
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
        world=WorldState.from_browser_page(
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


def test_reasoning_planner_rejects_non_positive_action_confidence():
    class BrowserReasoner(TaskReasoner):
        def reason(self, context):
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_navigate",
                        description="Navigate to the requested page.",
                        value="https://example.com",
                    ),
                ),
                rationale="Missing model confidence must fail closed.",
                confidence=0.0,
            )

    page = create_browser_page()
    planner = ReasoningTaskPlanner(BrowserReasoner())
    context = TaskPlanningContext(
        request_message="Otwórz stronę",
        intent="computer_use",
        browser_page=page,
        world=WorldState.from_browser_page(page),
    )

    assert planner.plan(context=context) is None
    assert planner.last_failure_reason == "non_positive_confidence"


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
        world=WorldState.from_browser_page(page),
    )

    payload = context.to_payload()
    serialized = json.dumps(payload)

    assert "provider" not in serialized
    assert "locator_value" not in serialized
    assert "strategy" not in serialized

# Generic Windows runtime wiring tests live in this existing CI-covered module.
import pytest

import app.agent.runtime.windows_desktop_agent_runtime as windows_runtime_factory
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def test_generic_windows_runtime_selects_navimind_before_openai(monkeypatch):
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "https://navimind.example/api/agent/task",
    )
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-shared-secret")
    monkeypatch.setenv("AGENT_TASK_REASONING", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.delenv("AGENT_PLAN_REASONING", raising=False)
    captured = {}

    monkeypatch.setattr(
        windows_runtime_factory,
        "_create_windows_desktop_control_loop",
        lambda *, plan_reasoner=None: captured.setdefault("plan_reasoner", plan_reasoner) or object(),
    )

    runtime = windows_runtime_factory.create_windows_desktop_agent_runtime()
    selected = runtime.orchestrator.task_planner.reasoner

    assert isinstance(selected, NaviMindTaskReasoner)
    assert selected.config.secret == "synthetic-shared-secret"
    assert runtime.orchestrator.require_task_reasoning is True
    assert captured["plan_reasoner"] is None


def test_generic_windows_runtime_fails_closed_without_navi_mind_secret(monkeypatch):
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "https://navimind.example/api/agent/task",
    )
    monkeypatch.delenv("NAVIMIND_AGENT_SECRET", raising=False)
    # Even an explicitly available OpenAI provider is not a silent fallback.
    monkeypatch.setenv("AGENT_TASK_REASONING", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-key")

    with pytest.raises(RuntimeError, match="NAVIMIND_AGENT_SECRET is required"):
        windows_runtime_factory.create_windows_desktop_agent_runtime()


def test_generic_windows_runtime_requires_explicit_task_reasoner(monkeypatch):
    monkeypatch.delenv("NAVIMIND_AGENT_URL", raising=False)
    monkeypatch.delenv("NAVIMIND_AGENT_SECRET", raising=False)
    monkeypatch.delenv("AGENT_TASK_REASONING", raising=False)

    with pytest.raises(RuntimeError, match="No task reasoner is configured"):
        windows_runtime_factory.create_windows_desktop_agent_runtime()


def test_generic_windows_navi_mind_contract_uses_fake_transport_only():
    captured = {}

    def fake_transport(request, timeout):
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Use the synthetic visible target.",
                "confidence": 0.96,
                "action": {
                    "name": "click_screen_element",
                    "description": "Click the synthetic visible button.",
                    "target": "Continue",
                    "value": None,
                },
                "requires_manual_review": False,
            }
        )

    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Synthetic Test App",
                active_window_title="Synthetic Test Window",
                screen_width=800,
                screen_height=600,
            ),
            metadata={"synthetic_fixture": True},
        ),
        elements=(
            ScreenElement(
                kind="button",
                label="Continue",
                confidence=0.99,
                interaction_capability=InteractionCapability.CLICKABLE,
                metadata={
                    "automation_id": "synthetic-only-id",
                    "runtime_id": "must-not-leave-local-runtime",
                },
            ),
        ),
    )
    context = TaskPlanningContext(
        request_message="Synthetic contract test only.",
        intent="computer_use",
        session_id="synthetic-session",
        capability_name="COMPUTER_USE",
        capability_description="Synthetic desktop capability.",
        skill_name="ComputerUseSkill",
        scene=scene,
    )
    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="https://navimind.example/api/agent/task",
            secret="synthetic-shared-secret",
            timeout_seconds=7,
        ),
        opener=fake_transport,
    )

    proposal = reasoner.reason(context)

    assert proposal is not None
    assert proposal.actions[0].target == "Continue"
    assert captured["timeout"] == 7
    assert captured["headers"]["X-navimind-agent-secret"] == "synthetic-shared-secret"
    serialized = json.dumps(captured["body"])
    assert "synthetic-only-id" not in serialized
    assert "must-not-leave-local-runtime" not in serialized
    assert "synthetic-shared-secret" not in serialized


def test_generic_windows_navi_mind_rejects_remote_http(monkeypatch):
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-shared-secret")
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "http://navimind.example/api/agent/task",
    )

    with pytest.raises(RuntimeError, match="must use HTTPS"):
        NaviMindTaskReasonerConfig.from_environment()

