from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest

from app.agent.agent_intent import AgentIntent
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.reasoning.plan_reasoner import PlanReasoner
from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)
from app.agent.reasoning.reasoning_plan_replanner import (
    ReasoningPlanReplanner,
)
from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)
from app.agent.runtime.execution_attempt import (
    ExecutionAttempt,
)
from app.agent.runtime.execution_context import (
    ExecutionContext,
)
from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)
from app.agent.execution.execution_result import (
    ExecutionResult,
)
from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)
from app.agent.verification.verification_result import (
    VerificationResult,
)


class RecordingReasoner(PlanReasoner):

    def __init__(
        self,
        proposal=None,
    ):
        self.proposal = proposal
        self.contexts = []

    def reason(self, context):
        self.contexts.append(context)
        return self.proposal


def create_context():
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHelper",
            active_window_title="WindowHelper - Quote",
            screen_width=1920,
            screen_height=1080,
        ),
    )

    scene = ScreenScene(
        observation=observation,
        metadata={
            "execution_runtime": {
                "generation": "fresh-7",
            },
        },
    )

    return ExecutionContext(
        request=AgentRequest(
            message="Przygotuj ofertę dla okna 1200x1500."
        ),
        last_observation=observation,
        current_scene=scene,
    )


def create_plan():
    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=(
            ActionStep(
                index=1,
                action=AgentAction(
                    name="failed_action",
                    description="Previous semantic step.",
                ),
            ),
        ),
        confidence=1.0,
    )


def create_execution_result():
    attempt = ExecutionAttempt(
        action=AgentAction(
            name="failed_action",
            description="Previous semantic step.",
        ),
        execution_result=ExecutionResult(
            action_name="failed_action",
            success=True,
            message="Action executed.",
        ),
        expected_outcome=ExpectedOutcome(
            description="Expected state",
        ),
        verification_result=VerificationResult(
            verified=False,
            reason="Expected element was not found.",
            confidence=0.9,
            metadata={
                "expected_label": "Zapisz",
                "found": False,
            },
        ),
        attempt_number=1,
    )

    return ExecutionLoopResult(
        attempts=(attempt,),
        success=False,
        stopped=True,
    )


def test_reasoning_replanner_builds_semantic_action_plan():
    reasoner = RecordingReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="open_save_workflow",
                    description=(
                        "Open the save workflow for the current quote."
                    ),
                ),
            ),
            rationale=(
                "The expected save control was not found, "
                "so use the semantic save workflow."
            ),
            confidence=0.82,
        )
    )

    replanner = ReasoningPlanReplanner(
        reasoner
    )

    context = create_context()

    result = replanner.replan(
        plan=create_plan(),
        failed_step=create_plan().steps[0],
        execution_result=create_execution_result(),
        context=context,
    )

    assert result is not None
    assert result.intent == AgentIntent.CREATE_QUOTE
    assert result.confidence == 0.82
    assert result.steps[0].action.name == (
        "open_save_workflow"
    )
    assert result.steps[0].action.requires_confirmation is False

    assert len(reasoner.contexts) == 1

    reasoning_context = reasoner.contexts[0]

    assert (
        reasoning_context.request_message
        == "Przygotuj ofertę dla okna 1200x1500."
    )
    assert (
        reasoning_context.failed_action_name
        == "failed_action"
    )
    assert (
        reasoning_context.verification_reason
        == "Expected element was not found."
    )

    payload = reasoning_context.to_payload()

    assert payload["intent"] == "create_quote"
    assert payload["verification"]["verified"] is False
    assert (
        payload["verification"]["metadata"]["found"]
        is False
    )
    assert (
        payload["scene"]["metadata"]["execution_runtime"]
        ["generation"]
        == "fresh-7"
    )


def test_reasoning_replanner_rejects_low_level_gui_proposal():
    reasoner = RecordingReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="mouse_click",
                    description="Click the save button.",
                ),
            ),
            rationale="Use a direct GUI click.",
            confidence=0.95,
        )
    )

    replanner = ReasoningPlanReplanner(
        reasoner
    )

    result = replanner.replan(
        plan=create_plan(),
        failed_step=create_plan().steps[0],
        execution_result=create_execution_result(),
        context=create_context(),
    )

    assert result is None


def test_reasoning_replanner_rejects_manual_review_proposal():
    reasoner = RecordingReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="request_operator_review",
                    description=(
                        "Ask the operator to inspect the workflow."
                    ),
                ),
            ),
            rationale="The state is ambiguous.",
            confidence=0.4,
            requires_manual_review=True,
        )
    )

    replanner = ReasoningPlanReplanner(
        reasoner
    )

    result = replanner.replan(
        plan=create_plan(),
        failed_step=create_plan().steps[0],
        execution_result=create_execution_result(),
        context=create_context(),
    )

    assert result is None


def test_reasoning_replanner_rejects_invalid_confidence():
    reasoner = RecordingReasoner(
        proposal=ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="recover_action",
                    description="Recover the workflow.",
                ),
            ),
            rationale="Recover.",
            confidence=1.5,
        )
    )

    replanner = ReasoningPlanReplanner(
        reasoner
    )

    result = replanner.replan(
        plan=create_plan(),
        failed_step=create_plan().steps[0],
        execution_result=create_execution_result(),
        context=create_context(),
    )

    assert result is None
