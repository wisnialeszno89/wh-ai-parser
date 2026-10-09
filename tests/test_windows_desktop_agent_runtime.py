import json

import pytest

import app.agent.runtime.windows_desktop_agent_runtime as runtime_factory
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.reasoning.task_planning_context import TaskPlanningContext


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeTaskReasoner(TaskReasoner):
    def reason(self, context):
        return ReasoningProposal(
            actions=(),
            rationale="Synthetic test provider.",
            confidence=1.0,
            requires_manual_review=True,
            status="done",
        )


def _fake_control_loop_factory(monkeypatch):
    captured = {}

    def factory(*, plan_reasoner=None):
        captured["plan_reasoner"] = plan_reasoner
        return object()

    monkeypatch.setattr(
        runtime_factory,
        "create_windows_desktop_agent_control_loop",
        factory,
    )
    return captured


def test_generic_windows_runtime_selects_navimind_and_passes_secret(monkeypatch):
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "https://navimind.example/api/agent/task",
    )
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-shared-secret")
    monkeypatch.setenv("AGENT_TASK_REASONING", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-key")
    monkeypatch.delenv("AGENT_PLAN_REASONING", raising=False)
    captured = _fake_control_loop_factory(monkeypatch)

    runtime = runtime_factory.create_windows_desktop_agent_runtime()

    selected = runtime.orchestrator.task_planner.reasoner
    assert isinstance(selected, NaviMindTaskReasoner)
    assert selected.config.url == "https://navimind.example/api/agent/task"
    assert selected.config.secret == "synthetic-shared-secret"
    assert runtime.orchestrator.require_task_reasoning is True
    assert captured["plan_reasoner"] is None


def test_navi_mind_configuration_fails_closed_without_secret(monkeypatch):
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "https://navimind.example/api/agent/task",
    )
    monkeypatch.delenv("NAVIMIND_AGENT_SECRET", raising=False)
    monkeypatch.setenv("AGENT_TASK_REASONING", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-key")

    with pytest.raises(RuntimeError, match="NAVIMIND_AGENT_SECRET is required"):
        runtime_factory.create_windows_desktop_agent_runtime()


def test_navi_mind_rejects_remote_http_and_embedded_url_credentials(monkeypatch):
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-shared-secret")
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "http://navimind.example/api/agent/task",
    )
    with pytest.raises(RuntimeError, match="must use HTTPS"):
        NaviMindTaskReasonerConfig.from_environment()

    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "https://user:password@navimind.example/api/agent/task",
    )
    with pytest.raises(RuntimeError, match="must not contain embedded credentials"):
        NaviMindTaskReasonerConfig.from_environment()


def test_navi_mind_allows_localhost_http_only_with_a_secret(monkeypatch):
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "http://localhost:3000/api/agent/task",
    )
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "local-synthetic-secret")
    config = NaviMindTaskReasonerConfig.from_environment()
    assert config.url == "http://localhost:3000/api/agent/task"
    assert config.secret == "local-synthetic-secret"


def test_generic_windows_runtime_requires_an_explicit_provider(monkeypatch):
    monkeypatch.delenv("NAVIMIND_AGENT_URL", raising=False)
    monkeypatch.delenv("NAVIMIND_AGENT_SECRET", raising=False)
    monkeypatch.delenv("AGENT_TASK_REASONING", raising=False)

    with pytest.raises(RuntimeError, match="No task reasoner is configured"):
        runtime_factory.create_windows_desktop_agent_runtime()


def test_openai_task_reasoner_is_an_explicit_alternative(monkeypatch):
    monkeypatch.delenv("NAVIMIND_AGENT_URL", raising=False)
    monkeypatch.delenv("NAVIMIND_AGENT_SECRET", raising=False)
    monkeypatch.setenv("AGENT_TASK_REASONING", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-key")
    captured = _fake_control_loop_factory(monkeypatch)
    sentinel = FakeTaskReasoner()
    monkeypatch.setattr(
        runtime_factory,
        "_openai_task_reasoner",
        lambda: sentinel,
    )

    runtime = runtime_factory.create_windows_desktop_agent_runtime()

    assert runtime.orchestrator.task_planner.reasoner is sentinel
    assert runtime.orchestrator.require_task_reasoning is True
    assert captured["plan_reasoner"] is None


def test_plan_reasoner_is_only_created_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv(
        "NAVIMIND_AGENT_URL",
        "https://navimind.example/api/agent/task",
    )
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-shared-secret")
    monkeypatch.delenv("AGENT_PLAN_REASONING", raising=False)
    captured = _fake_control_loop_factory(monkeypatch)

    runtime_factory.create_windows_desktop_agent_runtime()

    assert captured["plan_reasoner"] is None


def test_navi_mind_contract_smoke_uses_fake_transport_and_semantic_only_payload():
    captured = {}

    def fake_transport(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        body = json.loads(request.data.decode("utf-8"))
        captured["body"] = body
        return FakeResponse(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Click the synthetic visible button.",
                "confidence": 0.96,
                "action": {
                    "name": "click_screen_element",
                    "description": "Click the visible synthetic button.",
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
        request_message="Click the visible Continue button in the synthetic test.",
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
    assert proposal.status == "continue"
    assert proposal.actions[0].name == "click_screen_element"
    assert proposal.actions[0].target == "Continue"
    assert captured["url"] == "https://navimind.example/api/agent/task"
    assert captured["timeout"] == 7
    assert captured["headers"]["X-navimind-agent-secret"] == "synthetic-shared-secret"

    serialized = json.dumps(captured["body"])
    assert captured["body"]["world"]["visible_elements"][0]["label"] == "Continue"
    assert "synthetic-only-id" not in serialized
    assert "must-not-leave-local-runtime" not in serialized
    assert "synthetic-shared-secret" not in serialized
