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
    assert knowledge["version"] == "1"

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
    assert foundation["version"] == "1"
    assert "button" in foundation["ui_model"]
    assert "tabitem" in foundation["ui_model"]
