from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest

from app.agent.decision.decision_engine import (
    DecisionEngine,
)

from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_preparation_loop import (
    EnvironmentPreparationLoop,
)

from app.agent.environment.fake_environment_preparation_executor import (
    FakeEnvironmentPreparationExecutor,
)

from app.agent.environment.environment_readiness_evaluator import (
    EnvironmentReadinessEvaluator,
)

from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)

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


def create_observation():

    return EnvironmentObservation(
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
            message="Test request"
        )
    )


def create_plan(
    *actions: AgentAction,
):

    steps = tuple(
        ActionStep(
            index=index,
            action=action,
        )
        for index, action
        in enumerate(
            actions,
            start=1,
        )
    )

    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=steps,
        confidence=1.0,
    )


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
    )


def test_control_loop_executes_plan():

    loop = create_control_loop(
        SuccessfulExecutor()
    )

    action = AgentAction(
        name="first_action",
        description="First action",
    )

    plan = create_plan(
        action
    )

    result = loop.run(
        plan,
        create_context(),
    )

    assert result.success is True

    assert (
        result.executed_actions
        == 1
    )

    assert (
        len(result.decisions)
        == 1
    )


def test_control_loop_executes_multiple_actions():

    loop = create_control_loop(
        SuccessfulExecutor()
    )

    plan = create_plan(
        AgentAction(
            name="first_action",
            description="First action",
        ),
        AgentAction(
            name="second_action",
            description="Second action",
        ),
    )

    result = loop.run(
        plan,
        create_context(),
    )

    assert result.success is True

    assert (
        result.executed_actions
        == 2
    )

    assert (
        len(result.decisions)
        == 2
    )


def test_control_loop_stops_on_execution_failure():

    loop = create_control_loop(
        FailingExecutor()
    )

    plan = create_plan(
        AgentAction(
            name="failing_action",
            description="Failing action",
        ),
        AgentAction(
            name="second_action",
            description="Second action",
        ),
    )

    result = loop.run(
        plan,
        create_context(),
    )

    assert result.success is False

    assert result.stopped is True

    assert (
        result.executed_actions
        == 1
    )


def test_control_loop_requires_review_before_execution():

    loop = create_control_loop(
        SuccessfulExecutor()
    )

    action = AgentAction(
        name="protected_action",
        description="Protected action",
        requires_confirmation=True,
    )

    plan = create_plan(
        action
    )

    result = loop.run(
        plan,
        create_context(),
    )

    assert result.success is False

    assert (
        result.requires_manual_review
        is True
    )

    assert result.stopped is True

    assert (
        result.executed_actions
        == 0
    )


def test_control_loop_updates_context_perception():

    loop = create_control_loop(
        SuccessfulExecutor()
    )

    context = create_context()

    plan = create_plan(
        AgentAction(
            name="test_action",
            description="Test action",
        )
    )

    loop.run(
        plan,
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
