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
