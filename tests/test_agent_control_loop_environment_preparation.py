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

from app.agent.environment.environment_preparation_executor import (
    EnvironmentPreparationExecutor,
)

from app.agent.environment.environment_preparation_loop import (
    EnvironmentPreparationLoop,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)

from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_readiness_evaluator import (
    EnvironmentReadinessEvaluator,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
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

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.verification.expectation_resolver import (
    ExpectationResolver,
)

from app.agent.verification.outcome_verifier import (
    OutcomeVerifier,
)

from app.agent.runtime.verification_loop import (
    VerificationLoop,
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


class RecordingExecutor:

    def __init__(
        self,
    ) -> None:

        self.calls = 0

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

        self.calls += 1

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Action executed.",
        )


class FailingPreparationExecutor(
    EnvironmentPreparationExecutor
):

    def __init__(
        self,
    ) -> None:

        self.calls = 0

    def execute(
        self,
        preparation,
    ) -> EnvironmentPreparationResult:

        self.calls += 1

        return EnvironmentPreparationResult(
            success=False,
            reason="Preparation failed.",
        )


class NonSwitchingPreparationExecutor(
    EnvironmentPreparationExecutor
):

    def __init__(
        self,
    ) -> None:

        self.calls = 0

    def execute(
        self,
        preparation,
    ) -> EnvironmentPreparationResult:

        self.calls += 1

        return EnvironmentPreparationResult(
            success=True,
            reason=(
                "Preparation reported success "
                "but did not change environment."
            ),
        )


class SwitchingPreparationExecutor(
    EnvironmentPreparationExecutor
):

    def __init__(
        self,
        environment,
        target_application,
    ) -> None:

        self.environment = environment

        self.target_application = (
            target_application
        )

        self.calls = 0

    def execute(
        self,
        preparation,
    ) -> EnvironmentPreparationResult:

        self.calls += 1

        self.environment.state = (
            EnvironmentState(
                active_application=(
                    self.target_application
                ),
                active_window_title=(
                    f"{self.target_application} Window"
                ),
                screen_width=1920,
                screen_height=1080,
            )
        )

        return EnvironmentPreparationResult(
            success=True,
            reason=(
                "Environment switched successfully."
            ),
        )


def create_environment():

    return FakeEnvironment(
        state=EnvironmentState(
            active_application="Notepad",
            active_window_title=(
                "Notepad Window"
            ),
            screen_width=1920,
            screen_height=1080,
        )
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Integration test request"
        )
    )


def create_plan():

    action = AgentAction(
        name="create_quote",
        description=(
            "Create a quote in WindowHelper."
        ),
        environment_requirement=(
            EnvironmentRequirement(
                application="WindowHelper"
            )
        ),
    )

    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=(
            ActionStep(
                index=1,
                action=action,
            ),
        ),
        confidence=1.0,
    )


def create_control_loop(
    environment,
    preparation_executor,
    action_executor=None,
):

    environment_runtime = (
        EnvironmentRuntime(
            adapter=environment
        )
    )

    perception_engine = (
        PerceptionEngine()
    )

    execution_engine = (
        ExecutionEngine(
            ExecutorRegistry(
                executors=(
                    action_executor
                    if action_executor is not None
                    else SuccessfulExecutor(),
                )
            )
        )
    )

    verification_loop = (
        VerificationLoop(
            execution_engine=(
                execution_engine
            ),
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

    preparation_loop = (
        EnvironmentPreparationLoop(
            environment=environment,
            readiness_evaluator=(
                EnvironmentReadinessEvaluator()
            ),
            preparation_engine=(
                EnvironmentPreparationEngine()
            ),
            preparation_executor=(
                preparation_executor
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
        environment_preparation_loop=(
            preparation_loop
        ),
    )


def test_control_loop_prepares_environment_before_execution():

    environment = (
        create_environment()
    )

    preparation_executor = (
        SwitchingPreparationExecutor(
            environment,
            "WindowHelper",
        )
    )

    loop = create_control_loop(
        environment,
        preparation_executor,
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is True

    assert (
        result.executed_actions
        == 1
    )

    assert (
        preparation_executor.calls
        == 1
    )

    assert (
        environment.state
        .active_application
        == "WindowHelper"
    )


def test_control_loop_does_not_execute_when_preparation_fails():

    environment = (
        create_environment()
    )

    action_executor = (
        RecordingExecutor()
    )

    preparation_executor = (
        FailingPreparationExecutor()
    )

    loop = create_control_loop(
        environment,
        preparation_executor,
        action_executor,
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is False

    assert (
        result.executed_actions
        == 0
    )

    assert (
        preparation_executor.calls
        == 1
    )

    assert (
        action_executor.calls
        == 0
    )


def test_control_loop_does_not_execute_when_environment_stays_unready():

    environment = (
        create_environment()
    )

    action_executor = (
        RecordingExecutor()
    )

    preparation_executor = (
        NonSwitchingPreparationExecutor()
    )

    loop = create_control_loop(
        environment,
        preparation_executor,
        action_executor,
    )

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is False

    assert (
        result.executed_actions
        == 0
    )

    assert (
        preparation_executor.calls
        == 1
    )

    assert (
        action_executor.calls
        == 0
    )

    assert (
        environment.state
        .active_application
        == "Notepad"
    )
