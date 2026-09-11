from app.agent.agent_action import (
    AgentAction,
)

from app.agent.agent_intent import (
    AgentIntent,
)

from app.agent.agent_request import (
    AgentRequest,
)

from app.agent.decision.decision import (
    Decision,
)

from app.agent.decision.decision_type import (
    DecisionType,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.planning.action_step import (
    ActionStep,
)

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class SuccessfulEnvironmentRuntime:

    def observe(
        self,
    ) -> EnvironmentObservation:

        return EnvironmentObservation(
            state=EnvironmentState(
                active_window_title="Test Window",
                screen_width=1920,
                screen_height=1080,
            ),
        )


class SuccessfulPerceptionEngine:

    def perceive(
        self,
        observation: EnvironmentObservation,
    ):

        class Scene:

            def __init__(
                self,
                observation,
            ):

                self.observation = (
                    observation
                )

        return Scene(
            observation
        )


class ProceedDecisionEngine:

    def decide(
        self,
        action,
        context,
    ):

        return Decision(
            decision_type=(
                DecisionType.PROCEED
            ),
        )


class StopDecisionEngine:

    def decide(
        self,
        action,
        context,
    ):

        return Decision(
            decision_type=(
                DecisionType.STOP
            ),
        )


class ManualReviewDecisionEngine:

    def decide(
        self,
        action,
        context,
    ):

        return Decision(
            decision_type=(
                DecisionType.MANUAL_REVIEW
            ),
        )


class SuccessfulVerificationLoop:

    def run(
        self,
        action,
        context,
    ):

        from app.agent.runtime.execution_loop_result import (
            ExecutionLoopResult,
        )

        return ExecutionLoopResult(
            attempts=(),
            success=True,
        )


class FailingVerificationLoop:

    def run(
        self,
        action,
        context,
    ):

        from app.agent.runtime.execution_loop_result import (
            ExecutionLoopResult,
        )

        return ExecutionLoopResult(
            attempts=(),
            success=False,
        )


def create_plan():

    action = AgentAction(
        name="test_action",
        description="Test action",
    )

    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=(
            ActionStep(
                index=0,
                action=action,
            ),
        ),
        confidence=1.0,
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Test request",
        )
    )


def create_control_loop(
    *,
    decision_engine,
    verification_loop,
):

    return AgentControlLoop(
        environment_runtime=(
            SuccessfulEnvironmentRuntime()
        ),
        perception_engine=(
            SuccessfulPerceptionEngine()
        ),
        decision_engine=decision_engine,
        verification_loop=verification_loop,
    )


def test_control_loop_plan_lifecycle_starts_running():

    loop = create_control_loop(
        decision_engine=(
            ProceedDecisionEngine()
        ),
        verification_loop=(
            SuccessfulVerificationLoop()
        ),
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert (
        result.plan_status
        == ActionPlanStatus.COMPLETED
    )

    assert len(
        result.plan_transitions
    ) == 2

    assert (
        result.plan_transitions[0]
        .from_status
        == ActionPlanStatus.CREATED
    )

    assert (
        result.plan_transitions[0]
        .to_status
        == ActionPlanStatus.RUNNING
    )


def test_control_loop_plan_lifecycle_completes():

    loop = create_control_loop(
        decision_engine=(
            ProceedDecisionEngine()
        ),
        verification_loop=(
            SuccessfulVerificationLoop()
        ),
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is True

    assert (
        result.plan_status
        == ActionPlanStatus.COMPLETED
    )

    assert (
        result.plan_transitions[-1]
        .from_status
        == ActionPlanStatus.RUNNING
    )

    assert (
        result.plan_transitions[-1]
        .to_status
        == ActionPlanStatus.COMPLETED
    )


def test_control_loop_plan_lifecycle_stops():

    loop = create_control_loop(
        decision_engine=(
            StopDecisionEngine()
        ),
        verification_loop=(
            SuccessfulVerificationLoop()
        ),
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is False

    assert result.stopped is True

    assert (
        result.plan_status
        == ActionPlanStatus.STOPPED
    )

    assert (
        result.plan_transitions[-1]
        .from_status
        == ActionPlanStatus.RUNNING
    )

    assert (
        result.plan_transitions[-1]
        .to_status
        == ActionPlanStatus.STOPPED
    )


def test_control_loop_plan_lifecycle_requires_manual_review():

    loop = create_control_loop(
        decision_engine=(
            ManualReviewDecisionEngine()
        ),
        verification_loop=(
            SuccessfulVerificationLoop()
        ),
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is False

    assert (
        result.requires_manual_review
        is True
    )

    assert (
        result.plan_status
        == ActionPlanStatus.MANUAL_REVIEW
    )

    assert (
        result.plan_transitions[-1]
        .from_status
        == ActionPlanStatus.RUNNING
    )

    assert (
        result.plan_transitions[-1]
        .to_status
        == ActionPlanStatus.MANUAL_REVIEW
    )


def test_control_loop_plan_lifecycle_fails():

    loop = create_control_loop(
        decision_engine=(
            ProceedDecisionEngine()
        ),
        verification_loop=(
            FailingVerificationLoop()
        ),
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is False

    assert (
        result.plan_status
        == ActionPlanStatus.FAILED
    )

    assert (
        result.plan_transitions[-1]
        .from_status
        == ActionPlanStatus.RUNNING
    )

    assert (
        result.plan_transitions[-1]
        .to_status
        == ActionPlanStatus.FAILED
    )
