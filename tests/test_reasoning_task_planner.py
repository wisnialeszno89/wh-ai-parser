from app.agent.agent_intent import AgentIntent
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.reasoning_task_planner import (
    ReasoningTaskPlanner,
)
from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)
from app.agent.reasoning.task_reasoner import TaskReasoner

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


def create_context():
    return TaskPlanningContext(
        request_message="Otwórz nową ofertę",
        intent=AgentIntent.EXECUTE_IN_WH.value,
        capability_name="WH_WINDOW",
        capability_description=(
            "Controlled WindowHub execution."
        ),
        skill_name="WHWindowSkill",
    )


def test_reasoning_task_planner_builds_semantic_plan_with_target():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description=(
                        "Click the requested semantic UI control."
                    ),
                    target="NOWA OFERTA",
                ),
            ),
            rationale="Open a new offer in WindowHub.",
            confidence=0.93,
        )
    )

    planner = ReasoningTaskPlanner(reasoner)

    plan = planner.plan(
        context=create_context()
    )

    assert plan is not None
    assert plan.intent == AgentIntent.EXECUTE_IN_WH
    assert plan.confidence == 0.93
    assert len(plan.steps) == 1
    assert plan.steps[0].action.name == (
        "click_screen_element"
    )
    assert plan.steps[0].action.target == "NOWA OFERTA"

    payload = reasoner.contexts[0].to_payload()

    assert payload["request_message"] == (
        "Otwórz nową ofertę"
    )
    assert "window_handle" not in str(payload)
    assert "runtime_id" not in str(payload)
    assert "tracked_object_id" not in str(payload)


def test_reasoning_task_planner_rejects_low_level_target():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description="Click the target.",
                    target="window_handle=123",
                ),
            ),
            rationale="Unsafe low-level target.",
            confidence=0.9,
        )
    )

    planner = ReasoningTaskPlanner(reasoner)

    assert planner.plan(
        context=create_context()
    ) is None


def test_reasoning_task_planner_fails_closed_on_manual_review():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="ask_for_missing_information",
                    description=(
                        "Request the missing product choice."
                    ),
                ),
            ),
            rationale="The request is ambiguous.",
            confidence=0.42,
            requires_manual_review=True,
        )
    )

    planner = ReasoningTaskPlanner(reasoner)

    assert planner.plan(
        context=create_context()
    ) is None

def test_reasoning_task_planner_normalizes_semantic_open_new_offer():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="open_new_offer",
                    description=(
                        "Open the new offer form in WindowHub."
                    ),
                    target="Nowa oferta",
                ),
            ),
            rationale="The user asked to start a new offer.",
            confidence=0.98,
        )
    )

    planner = ReasoningTaskPlanner(reasoner)

    plan = planner.plan(
        context=create_context()
    )

    assert plan is not None
    assert len(plan.steps) == 1

    action = plan.steps[0].action
    assert action.name == "click_screen_element"
    assert action.target == "Nowa oferta"



def test_reasoning_task_planner_exposes_semantic_initial_scene_only():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="WindowHub - Oferta",
                screen_width=1920,
                screen_height=1080,
            ),
            metadata={
                "window_handle": 123,
                "screenshot": object(),
            },
        ),
        elements=(
            ScreenElement(
                kind="button",
                label="NOWA OFERTA",
                confidence=0.99,
                interaction_capability=(
                    InteractionCapability.CLICKABLE
                ),
                metadata={
                    "automation_id": "Nowa_oferta",
                    "runtime_id": "secret-runtime-id",
                },
            ),
        ),
    )

    context = TaskPlanningContext(
        request_message="Otwórz nową ofertę",
        intent=AgentIntent.EXECUTE_IN_WH.value,
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
        scene=scene,
    )

    payload = context.to_payload()

    assert payload["scene"]["active_application"] == "WindowHub"
    assert payload["scene"]["active_window_title"] == (
        "WindowHub - Oferta"
    )
    assert payload["scene"]["visible_elements"] == (
        [
            {
                "kind": "button",
                "label": "NOWA OFERTA",
                "interaction_capability": "clickable",
                "confidence": 0.99,
            }
        ]
    )

    serialized = str(payload)
    assert "window_handle" not in serialized
    assert "automation_id" not in serialized
    assert "runtime_id" not in serialized
    assert "screenshot" not in serialized


def test_reasoning_task_planner_normalizes_generic_click_with_semantic_target():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click",
                    description="Click the visible new offer control.",
                    target="NOWA OFERTA",
                ),
            ),
            rationale="Use the visible semantic control.",
            confidence=0.96,
        )
    )

    context = create_context()
    context = TaskPlanningContext(
        request_message=context.request_message,
        intent=context.intent,
        capability_name=context.capability_name,
        capability_description=context.capability_description,
        skill_name=context.skill_name,
        skill_description=context.skill_description,
        scene=ScreenScene(
            observation=EnvironmentObservation(
                state=EnvironmentState(
                    active_application="WindowHub",
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
        ),
    )

    plan = ReasoningTaskPlanner(reasoner).plan(
        context=context
    )

    assert plan is not None
    assert plan.steps[0].action.name == "click_screen_element"
    assert plan.steps[0].action.target == "NOWA OFERTA"


def test_reasoning_task_planner_rejects_technical_scene_target():
    reasoner = RecordingTaskReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click",
                    description="Click the new offer control.",
                    target="IDC_NEW",
                ),
            ),
            rationale="Technical identifier target.",
            confidence=0.96,
        )
    )

    assert ReasoningTaskPlanner(reasoner).plan(
        context=create_context()
    ) is None
