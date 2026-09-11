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

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)

from app.agent.runtime.action_failure_policy import (
    ActionFailurePolicy,
)

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.verification_loop import (
    VerificationLoop,
)

from app.agent.verification.expectation_resolver import (
    ExpectationResolver,
)

from app.agent.verification.outcome_verifier import (
    OutcomeVerifier,
)


class RecordingExecutor:
    """
    Executor that records executed actions.

    One configured action intentionally fails.
    """

    def __init__(
        self,
        failing_action_name: str,
    ) -> None:

        self.failing_action_name = (
            failing_action_name
        )

        self.executed_actions = []

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

        if (
            action.name
            == self.failing_action_name
        ):

            return ExecutionResult(
                action_name=action.name,
                success=False,
                message="Intentional failure.",
            )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Action executed.",
        )


class SkipFailurePolicy(
    ActionFailurePolicy
):
    """
    Test policy that skips failed actions.
    """

    def decide(
        self,
        action,
        execution_result,
        context,
    ):

        return ActionFailureDecision.SKIP


def create_environment():

    return FakeEnvironment(
        state=EnvironmentState(
            active_application="TestApp",
            active_window_title=(
                "Test Window"
            ),
            screen_width=1920,
            screen_height=1080,
        )
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Execute plan.",
        )
    )


def create_plan():

    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=(
            ActionStep(
                index=1,
                action=AgentAction(
                    name="first_action",
                    description="First action",
                ),
            ),
            ActionStep(
                index=2,
                action=AgentAction(
                    name="failing_action",
                    description="Failing action",
                ),
            ),
            ActionStep(
                index=3,
                action=AgentAction(
                    name="third_action",
                    description="Third action",
                ),
            ),
        ),
        confidence=1.0,
    )


def create_control_loop(
    executor,
):

    environment = create_environment()

    environment_runtime = (
        EnvironmentRuntime(
            adapter=environment
        )
    )

    perception_engine = (
        PerceptionEngine()
    )

    registry = ExecutorRegistry(
        executors=(executor,)
    )

    execution_engine = (
        ExecutionEngine(
            registry
        )
    )

    verification_loop = (
        VerificationLoop(
            execution_engine=execution_engine,
            environment=environment,
            perception_engine=(
                perception_engine
            ),
            expectation_resolver=(
                ExpectationResolver()
            ),
            outcome_verifier=(
                OutcomeVerifier()
            ),
        )
    )

    return AgentControlLoop(
        environment_runtime=(
            environment_runtime
        ),
        perception_engine=(
            perception_engine
        ),
        decision_engine=(
            DecisionEngine()
        ),
        verification_loop=(
            verification_loop
        ),
        action_failure_policy=(
            SkipFailurePolicy()
        ),
    )


def test_control_loop_skips_failed_action_and_continues():

    executor = RecordingExecutor(
        failing_action_name=(
            "failing_action"
        )
    )

    loop = create_control_loop(
        executor
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is True

    assert result.stopped is False

    assert (
        executor.executed_actions
        == [
            "first_action",
            "failing_action",
            "third_action",
        ]
    )

    assert (
        result.executed_actions
        == 3
    )

    assert (
        result.failed_actions
        == 1
    )

    assert (
        result.skipped_actions
        == 1
    )

    assert (
        len(
            result.failure_records
        )
        == 1
    )

    failure_record = (
        result.failure_records[0]
    )

    assert (
        failure_record.action_name
        == "failing_action"
    )

    assert (
        failure_record.reason
        == "Intentional failure."
    )

    assert (
        failure_record.decision
        == ActionFailureDecision.SKIP
    )
