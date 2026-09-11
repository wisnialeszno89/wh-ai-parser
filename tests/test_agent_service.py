from app.agent.agent_intent import AgentIntent
from app.agent.agent_service import AgentService


def test_agent_service_handles_quote_request():
    response = AgentService().handle_message(
        "Zrób wycenę okna"
    )

    assert response.intent == (
        AgentIntent.CREATE_QUOTE
    )

    assert response.confidence == 1.0

    assert len(response.actions) > 0


def test_agent_service_handles_unknown_request():
    response = AgentService().handle_message(
        "xyz completely unknown task"
    )

    assert response.intent == (
        AgentIntent.UNKNOWN
    )

    assert response.requires_manual_review is True

    assert response.confidence == 0.0
