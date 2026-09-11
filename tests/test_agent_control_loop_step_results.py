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

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
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
        action,
    ):

        return True

    def execute(
        self,
        action,
        context,
    ):

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Executed.",
        )


def create_loop():

    environment = FakeEnvironment(
        state=EnvironmentState(
            active_application="TestApp",
            active_window_title=(
                "Test Window"
            ),
            screen_width=1920,
            screen_height=1080,
        )
    )

    execution_engine = (
        ExecutionEngine(
            ExecutorRegistry(
                executors=(
                    SuccessfulExecutor(),
                )
            )
        )
    )

    verification_loop = (
        VerificationLoop(
            execution_engine=execution_engine,
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
        )
    )

    return AgentControlLoop(
        environment_runtime=(
            EnvironmentRuntime(
                adapter=environment
            )
        ),
        perception_engine=(
            PerceptionEngine()
        ),
        decision_engine=(
            DecisionEngine()
        ),
        verification_loop=(
            verification_loop
        ),
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Test request",
        )
    )


def create_plan():

    action = AgentAction(
        name="successful_action",
        description="Successful action",
    )

    return ActionPlan(
        intent=(
            AgentIntent.CREATE_QUOTE
        ),
        steps=(
            ActionStep(
                index=0,
                action=action,
            ),
        ),
        confidence=1.0,
    )


def test_control_loop_records_completed_step():

    result = (
        create_loop().run(
            create_plan(),
            create_context(),
        )
    )

    assert result.success is True

    assert (
        len(result.step_results)
        == 1
    )

    step_result = (
        result.step_results[0]
    )

    assert (
        step_result.action_name
        == "successful_action"
    )

    assert (
        step_result.status
        == ActionStepStatus.COMPLETED
    )
