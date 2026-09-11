from app.agent.agent_action import (
    AgentAction,
)

from app.agent.agent_intent import (
    AgentIntent,
)

from app.agent.agent_request import (
    AgentRequest,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
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

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.planning.action_step import (
    ActionStep,
)

from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
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


def create_environment(
    *,
    active_application: str = "TestApp",
):

    return FakeEnvironment(
        state=EnvironmentState(
            active_application=active_application,
            active_window_title="Test Window",
            screen_width=1920,
            screen_height=1080,
        )
    )


def create_execution_engine():

    registry = ExecutorRegistry(
        executors=(
            SuccessfulExecutor(),
        )
    )

    return ExecutionEngine(
        registry
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Execute action.",
        )
    )


def create_plan(
    action: AgentAction,
):

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


def test_default_control_loop_executes_ready_action():

    environment = create_environment(
        active_application="WindowHelper"
    )

    loop = (
        create_default_agent_control_loop(
            environment=environment,
            execution_engine=(
                create_execution_engine()
            ),
        )
    )

    action = AgentAction(
        name="test_action",
        description="Test action",
        environment_requirement=(
            EnvironmentRequirement(
                application="WindowHelper"
            )
        ),
    )

    result = loop.run(
        create_plan(action),
        create_context(),
    )

    assert result.success is True

    assert (
        result.executed_actions
        == 1
    )


def test_default_control_loop_stops_when_safe_runtime_cannot_prepare():

    environment = create_environment(
        active_application="OtherApp"
    )

    loop = (
        create_default_agent_control_loop(
            environment=environment,
            execution_engine=(
                create_execution_engine()
            ),
        )
    )

    action = AgentAction(
        name="test_action",
        description="Test action",
        environment_requirement=(
            EnvironmentRequirement(
                application="WindowHelper"
            )
        ),
    )

    result = loop.run(
        create_plan(action),
        create_context(),
    )

    assert result.success is False

    assert result.stopped is True

    assert (
        result.executed_actions
        == 0
    )
