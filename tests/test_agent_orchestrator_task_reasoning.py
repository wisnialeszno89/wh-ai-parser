from app.agent.agent_request import AgentRequest
from app.agent.runtime.agent_orchestrator import (
    AgentOrchestrator,
)
from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)
from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)
from app.agent.reasoning.task_reasoner import (
    TaskReasoner,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


class RecordingTaskReasoner(TaskReasoner):

    def __init__(self, proposal=None):
        self.proposal = proposal
        self.contexts = []

    def reason(self, context):
        self.contexts.append(context)
        return self.proposal


def test_orchestrator_uses_initial_task_reasoner_plan():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description="Open the new offer control.",
                    target="CUSTOM TARGET",
                ),
            ),
            rationale="Semantic task reasoning.",
            confidence=0.91,
        )
    )

    orchestrator = AgentOrchestrator(
        task_reasoner=reasoner
    )

    context = orchestrator.prepare(
        AgentRequest(
            message="Otwórz nową ofertę"
        )
    )

    assert context.intent.value == "execute_in_wh"
    assert context.plan is not None
    assert context.plan.steps[0].action.name == (
        "click_screen_element"
    )
    assert context.plan.steps[0].action.target == (
        "CUSTOM TARGET"
    )
    assert context.plan.confidence == 0.91

    assert len(reasoner.contexts) == 1
    assert reasoner.contexts[0].capability_name == (
        "WH_WINDOW"
    )


def test_orchestrator_falls_back_to_existing_skill_planner():
    reasoner = RecordingTaskReasoner(
        proposal=None
    )

    orchestrator = AgentOrchestrator(
        task_reasoner=reasoner
    )

    context = orchestrator.prepare(
        AgentRequest(
            message="Otwórz nową ofertę"
        )
    )

    assert context.plan is not None
    assert context.plan.steps[0].action.name == (
        "click_screen_element"
    )
    assert context.plan.steps[0].action.target == (
        "NOWA OFERTA"
    )


def test_orchestrator_passes_initial_scene_to_task_reasoner():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description="Open the visible new offer control.",
                    target="NOWA OFERTA",
                ),
            ),
            rationale="Use the currently observed WindowHub control.",
            confidence=0.97,
        )
    )

    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="WindowHub - Oferta",
            ),
        ),
        elements=(
            ScreenElement(
                kind="button",
                label="NOWA OFERTA",
                confidence=0.99,
                interaction_capability=(
                    InteractionCapability.CLICKABLE
                ),
            ),
        ),
    )

    orchestrator = AgentOrchestrator(
        task_reasoner=reasoner
    )

    context = orchestrator.prepare(
        AgentRequest(
            message="Otwórz nową ofertę"
        ),
        initial_scene=scene,
    )

    assert context.plan is not None
    assert len(reasoner.contexts) == 1
    assert reasoner.contexts[0].scene is scene

    payload = reasoner.contexts[0].to_payload()
    assert payload["scene"]["visible_elements"][0]["label"] == (
        "NOWA OFERTA"
    )
