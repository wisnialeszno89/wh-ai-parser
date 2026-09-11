from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest

from app.agent.runtime.agent_runtime import (
    AgentRuntime,
)


def test_runtime_executes_quote_request():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert (
        result.intent
        == AgentIntent.CREATE_QUOTE
    )

    assert result.executed is True

    assert (
        result.execution_report
        is not None
    )


def test_runtime_returns_execution_report():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    assert (
        result.execution_report
        is not None
    )

    assert (
        len(
            result.execution_report.results
        )
        > 0
    )


def test_runtime_executes_wh_plan():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    names = [
        item.action_name
        for item in (
            result.execution_report.results
        )
    ]

    assert (
        "analyze_request"
        in names
    )

    assert (
        "collect_offer_context"
        in names
    )

    assert (
        "validate_offer"
        in names
    )

    assert (
        "build_construction"
        in names
    )

    assert (
        "prepare_quote"
        in names
    )


def test_runtime_requires_manual_review_for_unknown():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message=(
                "xyz completely unknown "
                "agent command"
            )
        )
    )

    assert (
        result.intent
        == AgentIntent.UNKNOWN
    )

    assert (
        result.requires_manual_review
        is True
    )

    assert (
        result.executed
        is False
    )

    assert (
        result.execution_report
        is None
    )
