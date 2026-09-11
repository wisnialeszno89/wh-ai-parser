from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest

from app.agent.runtime.agent_orchestrator import (
    AgentOrchestrator,
)


def test_quote_request_selects_wh_skill():
    orchestrator = AgentOrchestrator()

    context = orchestrator.prepare(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert context.intent == (
        AgentIntent.CREATE_QUOTE
    )

    assert context.capability is not None
    assert context.skill is not None

    assert context.capability.name == (
        "WH_WINDOW"
    )


def test_quote_request_produces_plan():
    orchestrator = AgentOrchestrator()

    context = orchestrator.prepare(
        AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    names = [
        step.action.name
        for step in context.plan.steps
    ]

    assert "collect_offer_context" in names
    assert "validate_offer" in names
    assert "build_construction" in names
    assert "prepare_quote" in names


def test_unknown_request_requires_manual_review():
    orchestrator = AgentOrchestrator()

    context = orchestrator.prepare(
        AgentRequest(
            message="asdfgh xyz"
        )
    )

    assert context.intent == (
        AgentIntent.UNKNOWN
    )

    assert context.capability is None
    assert context.skill is None

    assert context.requires_manual_review is True


def test_capability_is_resolved_before_skill():
    orchestrator = AgentOrchestrator()

    context = orchestrator.prepare(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert context.capability is not None
    assert context.skill is not None

    assert (
        context.skill.capability_name
        == context.capability.name
    )


def test_execution_context_preserves_request():
    orchestrator = AgentOrchestrator()

    request = AgentRequest(
        message="Zrób wycenę okna"
    )

    context = orchestrator.prepare(
        request
    )

    assert context.request == request
