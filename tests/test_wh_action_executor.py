import pytest

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest

from app.agent.execution.wh_action_executor import (
    WHActionExecutor,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


def build_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Prepare quote"
        )
    )


@pytest.mark.parametrize(
    "action_name",
    (
        "analyze_request",
        "collect_offer_context",
        "validate_offer",
        "build_construction",
        "prepare_quote",
    ),
)
def test_wh_executor_supports_wh_actions(
    action_name,
):

    executor = WHActionExecutor()

    action = AgentAction(
        name=action_name,
        description="Test action",
    )

    assert executor.supports(action) is True


def test_wh_executor_rejects_unknown_action():

    executor = WHActionExecutor()

    action = AgentAction(
        name="write_word_document",
        description="Word action",
    )

    assert executor.supports(action) is False


def test_prepare_quote_requires_review():

    executor = WHActionExecutor()

    context = build_context()

    result = executor.execute(
        AgentAction(
            name="prepare_quote",
            description="Prepare quote",
        ),
        context,
    )

    assert result.success is True

    assert result.requires_manual_review is True

    assert (
        context.get_value("quote_prepared")
        is True
    )


def test_build_construction_updates_context():

    executor = WHActionExecutor()

    context = build_context()

    result = executor.execute(
        AgentAction(
            name="build_construction",
            description="Build construction",
        ),
        context,
    )

    assert result.success is True

    assert (
        context.get_value(
            "construction_build_started"
        )
        is True
    )

    assert (
        result.metadata["workflow_stage"]
        == "construction"
    )
