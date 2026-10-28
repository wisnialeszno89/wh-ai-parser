from app.agent.agent_request import AgentRequest
from app.agent.knowledge.computer_foundation import (
    build_local_knowledge,
    get_computer_foundation_knowledge,
)
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator


class _CapturingReasoner(TaskReasoner):
    def __init__(self):
        self.context = None

    def reason(self, context):
        self.context = context
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description="Click the visible OK control.",
                    target="OK",
                ),
            ),
            rationale="Use the visible semantic control.",
            confidence=0.95,
        )


def test_computer_foundation_contains_core_gui_knowledge():
    knowledge = get_computer_foundation_knowledge()

    assert knowledge["name"] == "Computer Foundation"
    assert knowledge["version"] == "2"

    ui_model = knowledge["ui_model"]

    for control in (
        "button",
        "tabitem",
        "edit",
        "checkbox",
        "combobox",
        "listitem",
        "menuitem",
        "radiobutton",
    ):
        assert control in ui_model

    assert "verification_rules" in knowledge
    assert "ambiguity_rules" in knowledge
    assert "execution_boundary" in knowledge


def test_computer_foundation_covers_windows_linux_and_macos():
    knowledge = get_computer_foundation_knowledge()

    platforms = knowledge["platforms"]
    assert set(platforms) == {"windows", "linux", "macos"}

    assert "File Explorer" in platforms["windows"]["common_surfaces"]
    assert "/home/<user>" in platforms["linux"]["path_conventions"]
    assert "/Users/<user>" in platforms["macos"]["path_conventions"]

    for platform in platforms.values():
        assert platform["safety"]
        assert platform["navigation_conventions"]


def test_computer_foundation_prioritizes_observed_state_and_approved_capabilities():
    knowledge = get_computer_foundation_knowledge()

    cross_platform = knowledge["cross_platform_model"]
    assert "observed world" in cross_platform["environment_discovery"]
    assert "approved filesystem adapter" in cross_platform["paths_and_storage"]
    assert "not proof" in cross_platform["capability_discovery"]

    missions = knowledge["mission_patterns"]
    assert "sending" in missions["email_and_messaging"]
    assert "verify" in missions["spreadsheets"]
    assert "untrusted data" in missions["browser_work"]


def test_computer_foundation_returns_isolated_copy():
    first = get_computer_foundation_knowledge()
    second = get_computer_foundation_knowledge()

    first["ui_model"]["button"] = "changed"

    assert (
        second["ui_model"]["button"]
        != "changed"
    )


def test_build_local_knowledge_preserves_application_knowledge():
    application = {
        "application": "WindowHub",
        "workflow": "quotation",
    }

    local = build_local_knowledge(application)

    assert local["application"] == "WindowHub"
    assert local["workflow"] == "quotation"
    assert "computer_foundation" in local


def test_orchestrator_injects_computer_foundation_into_reasoning_context():
    reasoner = _CapturingReasoner()

    orchestrator = AgentOrchestrator(
        task_reasoner=reasoner,
    )

    orchestrator.prepare(
        AgentRequest(
            message="Kliknij OK",
        ),
        application_knowledge={
            "application": "WindowHub",
            "workflow": "quotation",
        },
    )

    assert reasoner.context is not None
    local = reasoner.context.application_knowledge

    assert local is not None
    assert local["application"] == "WindowHub"
    assert local["workflow"] == "quotation"

    foundation = local["computer_foundation"]

    assert foundation["name"] == "Computer Foundation"
    assert foundation["version"] == "2"
    assert "button" in foundation["ui_model"]
    assert "tabitem" in foundation["ui_model"]
