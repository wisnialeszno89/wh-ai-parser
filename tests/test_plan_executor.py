from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest

from app.agent.execution.action_executor import (
    ActionExecutor,
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

from app.agent.execution.plan_executor import (
    PlanExecutor,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.planning.action_step import (
    ActionStep,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class SuccessfulExecutor(ActionExecutor):

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

        context.set_value(
            action.name,
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Executed",
        )


class FailingExecutor(ActionExecutor):

    def supports(
        self,
        action: AgentAction,
    ) -> bool:
        return action.name == "fail"

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        return ExecutionResult(
            action_name=action.name,
            success=False,
            message="Failed",
            requires_manual_review=True,
        )


def build_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Test"
        )
    )


def build_plan():

    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        confidence=1.0,
        requires_manual_review=False,
        steps=(
            ActionStep(
                index=1,
                action=AgentAction(
                    name="first",
                    description="First",
                ),
            ),
            ActionStep(
                index=2,
                action=AgentAction(
                    name="second",
                    description="Second",
                ),
            ),
        ),
    )


def test_plan_executor_executes_all_steps():

    registry = ExecutorRegistry(
        executors=(
            SuccessfulExecutor(),
        )
    )

    executor = PlanExecutor(
        ExecutionEngine(registry)
    )

    context = build_context()

    report = executor.execute(
        build_plan(),
        context,
    )

    assert report.success is True
    assert len(report.results) == 2

    assert (
        context.get_value("first")
        is True
    )

    assert (
        context.get_value("second")
        is True
    )


def test_plan_executor_stops_on_failure():

    registry = ExecutorRegistry(
        executors=(
            FailingExecutor(),
            SuccessfulExecutor(),
        )
    )

    plan = ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        confidence=1.0,
        requires_manual_review=False,
        steps=(
            ActionStep(
                index=1,
                action=AgentAction(
                    name="first",
                    description="First",
                ),
            ),
            ActionStep(
                index=2,
                action=AgentAction(
                    name="fail",
                    description="Fail",
                ),
            ),
            ActionStep(
                index=3,
                action=AgentAction(
                    name="third",
                    description="Third",
                ),
            ),
        ),
    )

    executor = PlanExecutor(
        ExecutionEngine(registry)
    )

    report = executor.execute(
        plan,
        build_context(),
    )

    assert len(report.results) == 2

    assert report.success is False

    assert (
        report.requires_manual_review
        is True
    )
