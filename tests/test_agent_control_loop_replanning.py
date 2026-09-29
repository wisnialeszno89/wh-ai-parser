from app.agent.agent_action import (
    AgentAction,
)

from app.agent.agent_intent import (
    AgentIntent,
)

from app.agent.agent_request import (
    AgentRequest,
)

from app.agent.decision.decision_engine import (
    DecisionEngine,
)

from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.environment.fake_environment import (
    FakeEnvironment,
)

from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.execution.execution_result import (
    ExecutionResult,
)

from app.agent.execution.executor_registry import (
    ExecutorRegistry,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.planning.action_step import (
    ActionStep,
)

from app.agent.planning.plan_replanner import (
    PlanReplanner,
)

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)

from app.agent.runtime.verification_loop import (
    VerificationLoop,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)

from app.agent.verification.expectation_resolver import (
    ExpectationResolver,
)

from app.agent.verification.outcome_verifier import (
    OutcomeVerifier,
)

from app.agent.verification.verification_result import (
    VerificationResult,
)


class RecordingExecutor:

    def __init__(
        self,
        *,
        fail_execution: bool = False,
    ) -> None:
        self.executed_actions = []
        self.fail_execution = fail_execution

    def supports(
        self,
        action: AgentAction,
    ) -> bool:
        return True

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        self.executed_actions.append(
            action.name
        )

        return ExecutionResult(
            action_name=action.name,
            success=not self.fail_execution,
            message=(
                "Execution failed."
                if self.fail_execution
                else "Execution succeeded."
            ),
        )


class StaticExpectationResolver:

    def resolve(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome:
        return ExpectedOutcome(
            description="verification required"
        )


class SequencedOutcomeVerifier:

    def __init__(self) -> None:
        self.calls = 0

    def verify(
        self,
        expected: ExpectedOutcome,
        scene,
    ) -> VerificationResult:
        self.calls += 1

        if self.calls == 1:
            return VerificationResult(
                verified=False,
                reason="Expected state was not reached.",
            )

        return VerificationResult(
            verified=True,
            reason="Expected state reached.",
        )


class RecordingReplanner(
    PlanReplanner
):

    def __init__(self) -> None:
        self.calls = []

    def replan(
        self,
        *,
        plan,
        failed_step,
        execution_result,
        context,
    ):
        verification_result = (
            execution_result
            .last_attempt
            .verification_result
        )

        self.calls.append(
            (
                failed_step.action.name,
                verification_result.reason,
            )
        )

        return ActionPlan(
            intent=plan.intent,
            steps=(
                ActionStep(
                    index=1,
                    action=AgentAction(
                        name="recover_action",
                        description=(
                            "Execute the recovery strategy."
                        ),
                    ),
                ),
            ),
            confidence=0.9,
        )


def create_environment():
    return FakeEnvironment(
        state=EnvironmentState(
            active_application="TestApp",
            active_window_title="Test Window",
            screen_width=1920,
            screen_height=1080,
        )
    )


def create_context():
    return ExecutionContext(
        request=AgentRequest(
            message="Replan test request"
        )
    )


def create_plan():
    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=(
            ActionStep(
                index=1,
                action=AgentAction(
                    name="failed_action",
                    description="Action whose outcome will not verify.",
                ),
            ),
            ActionStep(
                index=2,
                action=AgentAction(
                    name="old_next_action",
                    description="Original next step.",
                ),
            ),
        ),
        confidence=1.0,
    )


def create_control_loop(
    *,
    executor,
    replanner=None,
    outcome_verifier=None,
):
    environment = create_environment()

    perception_engine = PerceptionEngine()

    verification_loop = VerificationLoop(
        execution_engine=ExecutionEngine(
            ExecutorRegistry(
                executors=(executor,)
            )
        ),
        environment=environment,
        perception_engine=perception_engine,
        expectation_resolver=(
            StaticExpectationResolver()
        ),
        outcome_verifier=(
            outcome_verifier
            if outcome_verifier is not None
            else OutcomeVerifier()
        ),
        max_attempts=1,
    )

    return AgentControlLoop(
        environment_runtime=EnvironmentRuntime(
            adapter=environment
        ),
        perception_engine=perception_engine,
        decision_engine=DecisionEngine(),
        verification_loop=verification_loop,
        replanner=replanner,
        max_replans=1,
    )


def test_control_loop_replans_after_failed_verification():
    executor = RecordingExecutor()

    replanner = RecordingReplanner()

    loop = create_control_loop(
        executor=executor,
        replanner=replanner,
        outcome_verifier=(
            SequencedOutcomeVerifier()
        ),
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is True

    assert executor.executed_actions == [
        "failed_action",
        "recover_action",
    ]

    assert "old_next_action" not in (
        executor.executed_actions
    )

    assert result.replanned_actions == 1

    assert len(replanner.calls) == 1

    assert replanner.calls[0] == (
        "failed_action",
        "Expected state was not reached.",
    )

    assert len(result.replan_records) == 1

    assert (
        result.replan_records[0]
        .replacement_actions
        == ("recover_action",)
    )

    assert (
        result.failure_records[0]
        .decision
        == ActionFailureDecision.REPLAN
    )


def test_control_loop_does_not_replan_execution_failure():
    executor = RecordingExecutor(
        fail_execution=True
    )

    replanner = RecordingReplanner()

    loop = create_control_loop(
        executor=executor,
        replanner=replanner,
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is False

    assert executor.executed_actions == [
        "failed_action",
    ]

    assert replanner.calls == []

    assert result.replanned_actions == 0
