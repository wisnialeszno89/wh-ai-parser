from app.agent.agent_request import AgentRequest
from app.agent.core.agent_session import AgentSession
from app.agent.session.agent_session_store import AgentSessionStore
from app.agent.offers.offer_workflow_service import OfferWorkflowService


def test_offer_session_keeps_context_between_messages():

    store = AgentSessionStore()
    session = store.get_or_create(
        session_id="offer-1"
    )

    service = OfferWorkflowService()

    first = service.process(
        session.state.offer_session,
        "Potrzebuję okno 1200x1500",
    )

    second = service.process(
        session.state.offer_session,
        "DKR, 2 sztuki",
    )

    assert first.current_context is not None
    assert second.current_context is not None

    context = second.current_context

    assert context.width == 1200
    assert context.height == 1500
    assert context.quantity == 2
    assert context.product_type == "window"
    assert context.opening == "RIGHT_TILT_TURN"


def test_agent_request_contains_session_information():

    request = AgentRequest(
        message="DKR, 2 sztuki",
        session_id="offer-1",
        salesman_id="salesman-1",
    )

    assert request.session_id == "offer-1"
    assert request.salesman_id == "salesman-1"
    assert request.message == "DKR, 2 sztuki"


def test_agent_runtime_keeps_offer_context_between_messages():

    from app.agent.runtime.agent_runtime import AgentRuntime

    runtime = AgentRuntime()
    session_id = "runtime-offer-1"

    first = runtime.run(
        AgentRequest(
            message="Potrzebuję okno 1200x1500",
            session_id=session_id,
            salesman_id="salesman-1",
        )
    )

    second = runtime.run(
        AgentRequest(
            message="DKR, 2 sztuki",
            session_id=session_id,
            salesman_id="salesman-1",
        )
    )

    assert first.intent.value == "create_quote"
    assert second.intent.value == "create_quote"

    context = second.context.get_value(
        "offer_context"
    )

    assert context is not None
    assert context.width == 1200
    assert context.height == 1500
    assert context.quantity == 2
    assert context.product_type == "window"
    assert context.opening == "RIGHT_TILT_TURN"


def test_offer_modifier_without_active_session_is_not_treated_as_quote():

    from app.agent.runtime.agent_runtime import AgentRuntime

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="DKR, 2 sztuki",
        )
    )

    assert result.intent.value == "unknown"
    assert result.executed is False
    assert result.requires_manual_review is True
