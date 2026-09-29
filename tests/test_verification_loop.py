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

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)

from app.agent.verification.verification_result import (
    VerificationResult,
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


class RuntimeAwareExecutor:

    def __init__(self):
        self.seen_generations = []

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
        self.seen_generations.append(
            context.get_value("generation")
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Action executed.",
        )


class SequencedPerceptionEngine:

    def __init__(self):
        self.calls = 0

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> ScreenScene:
        self.calls += 1

        return ScreenScene(
            observation=observation,
            metadata={
                "execution_runtime": {
                    "generation": f"fresh-{self.calls}",
                },
            },
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

    def __init__(self):
        self.calls = 0

    def verify(
        self,
        expected: ExpectedOutcome,
        scene: ScreenScene,
    ) -> VerificationResult:
        self.calls += 1

        if self.calls == 1:
            return VerificationResult(
                verified=False,
                reason="First verification intentionally fails.",
            )

        return VerificationResult(
            verified=True,
            reason="Second verification succeeds.",
        )


def test_retry_uses_fresh_runtime_state_from_reperception():

    executor = RuntimeAwareExecutor()

    registry = ExecutorRegistry(
        executors=(executor,)
    )

    environment = FakeEnvironment(
        state=create_observation().state
    )

    perception_engine = SequencedPerceptionEngine()

    loop = VerificationLoop(
        execution_engine=ExecutionEngine(
            registry
        ),
        environment=environment,
        perception_engine=perception_engine,
        expectation_resolver=StaticExpectationResolver(),
        outcome_verifier=SequencedOutcomeVerifier(),
        max_attempts=2,
    )

    context = create_context()
    context.set_value(
        "generation",
        "stale",
    )

    result = loop.run(
        create_action(),
        context,
    )

    assert result.success is True
    assert result.attempts[-1].verification_result is not None
    assert result.attempts[-1].verification_result.verified is True
    assert len(result.attempts) == 2
    assert executor.seen_generations == (
        ["stale", "fresh-1"]
    )
    assert (
        context.get_value("generation")
        == "fresh-2"
    )
