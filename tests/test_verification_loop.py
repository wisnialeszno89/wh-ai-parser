from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest

from app.agent.environment.fake_environment import (
    FakeEnvironment,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.execution.executor_registry import (
    ExecutorRegistry,
)

from app.agent.execution.execution_result import (
    ExecutionResult,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
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


class SuccessfulExecutor:

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

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Action executed.",
        )


class FailingExecutor:

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

        return ExecutionResult(
            action_name=action.name,
            success=False,
            message="Action failed.",
        )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Test request"
        )
    )


def create_observation():

    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="TestApp",
            active_window_title="Test Window",
            screen_width=1920,
            screen_height=1080,
        )
    )


def create_loop(
    executor,
    *,
    max_attempts=2,
):

    registry = ExecutorRegistry(
        executors=(executor,)
    )

    engine = ExecutionEngine(
        registry
    )

    environment = FakeEnvironment(
        state=create_observation().state
    )

    return VerificationLoop(
        execution_engine=engine,
        environment=environment,
        perception_engine=(
            PerceptionEngine()
        ),
        expectation_resolver=(
            ExpectationResolver()
        ),
        outcome_verifier=(
            OutcomeVerifier()
        ),
        max_attempts=max_attempts,
    )


def create_action():

    return AgentAction(
        name="test_action",
        description="Test action",
    )


def test_loop_executes_action():

    loop = create_loop(
        SuccessfulExecutor()
    )

    result = loop.run(
        create_action(),
        create_context(),
    )

    assert len(
        result.attempts
    ) >= 1


def test_loop_records_execution_result():

    loop = create_loop(
        SuccessfulExecutor()
    )

    result = loop.run(
        create_action(),
        create_context(),
    )

    attempt = result.last_attempt

    assert attempt is not None

    assert (
        attempt.execution_result.success
        is True
    )


def test_loop_stops_on_execution_failure():

    loop = create_loop(
        FailingExecutor()
    )

    result = loop.run(
        create_action(),
        create_context(),
    )

    assert result.success is False

    assert result.stopped is True

    assert len(
        result.attempts
    ) == 1


def test_loop_updates_context_perception():

    loop = create_loop(
        SuccessfulExecutor()
    )

    context = create_context()

    loop.run(
        create_action(),
        context,
    )

    assert (
        context.last_observation
        is not None
    )

    assert (
        context.current_scene
        is not None
    )


def test_loop_respects_max_attempts():

    loop = create_loop(
        SuccessfulExecutor(),
        max_attempts=2,
    )

    result = loop.run(
        create_action(),
        create_context(),
    )

    assert len(
        result.attempts
    ) <= 2
