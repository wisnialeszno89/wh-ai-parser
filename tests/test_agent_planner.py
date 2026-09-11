from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.agent_planner import AgentPlanner


def test_detects_quote_intent():
    planner = AgentPlanner()

    intent = planner.detect_intent(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert intent == AgentIntent.CREATE_QUOTE


def test_quote_plan_contains_offer_actions():
    planner = AgentPlanner()

    plan = planner.plan(
        AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    names = [
        step.action.name
        for step in plan.steps
    ]

    assert plan.intent == AgentIntent.CREATE_QUOTE
    assert "collect_offer_context" in names
    assert "validate_offer" in names
    assert "build_construction" in names


def test_detects_technical_question():
    planner = AgentPlanner()

    intent = planner.detect_intent(
        AgentRequest(
            message=(
                "Czy przy tym HST można "
                "zastosować taki profil?"
            )
        )
    )

    assert intent == AgentIntent.CHECK_TECHNICAL


def test_detects_market_request():
    planner = AgentPlanner()

    intent = planner.detect_intent(
        AgentRequest(
            message=(
                "Sprawdź ceny rynku niemieckiego"
            )
        )
    )

    assert intent == AgentIntent.CHECK_MARKET


def test_unknown_request_requires_manual_review():
    planner = AgentPlanner()

    plan = planner.plan(
        AgentRequest(
            message="asdasdasd"
        )
    )

    assert plan.intent == AgentIntent.UNKNOWN
    assert plan.requires_manual_review is True
