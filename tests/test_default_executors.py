from app.agent.agent_action import AgentAction

from app.agent.execution.default_executors import (
    create_default_executor_registry,
)


def test_default_registry_resolves_wh_executor():

    registry = (
        create_default_executor_registry()
    )

    action = AgentAction(
        name="build_construction",
        description="Build construction",
    )

    executor = registry.resolve(
        action
    )

    assert executor is not None
    assert executor.__class__.__name__ == (
        "WHActionExecutor"
    )
