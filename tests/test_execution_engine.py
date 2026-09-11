from app.agent.agent_action import AgentAction
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

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class FakeExecutor(ActionExecutor):

    def supports(
        self,
        action: AgentAction,
    ) -> bool:
        return action.name == "prepare_quote"

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        context.set_value(
            "executed",
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Quote prepared",
        )


def build_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Prepare quote"
        )
    )


def test_engine_executes_supported_action():

    registry = ExecutorRegistry(
        executors=(
            FakeExecutor(),
        )
    )

    engine = ExecutionEngine(
        registry=registry
    )

    context = build_context()

    result = engine.execute(
        AgentAction(
            name="prepare_quote",
            description="Prepare quote",
        ),
        context,
    )

    assert result.success is True
    assert result.message == "Quote prepared"

    assert (
        context.get_value("executed")
        is True
    )


def test_engine_requires_review_without_executor():

    registry = ExecutorRegistry()

    engine = ExecutionEngine(
        registry=registry
    )

    result = engine.execute(
        AgentAction(
            name="unknown_action",
            description="Unknown",
        ),
        build_context(),
    )

    assert result.success is False
    assert result.requires_manual_review is True
