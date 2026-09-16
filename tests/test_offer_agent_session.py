from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_context import (
    OfferContext,
)


def test_session_defaults_to_no_context():

    session = OfferAgentSession()

    assert session.current_context is None


def test_session_stores_current_context():

    context = OfferContext(
        raw_request=(
            "Potrzebuję okno 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
    )

    session = OfferAgentSession(
        current_context=context,
    )

    assert (
        session.current_context
        == context
    )


def test_session_context_can_be_updated():

    session = OfferAgentSession()

    context = OfferContext(
        raw_request=(
            "Potrzebuję okno 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
    )

    session.current_context = context

    assert (
        session.current_context
        == context
    )


from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


def test_session_defaults_to_new_workflow_state():

    session = OfferAgentSession()

    assert (
        session.workflow_state
        == OfferWorkflowState.NEW
    )


def test_session_stores_workflow_state():

    session = OfferAgentSession(
        workflow_state=(
            OfferWorkflowState.READY_FOR_PRICING
        ),
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.READY_FOR_PRICING
    )


def test_session_workflow_state_can_be_updated():

    session = OfferAgentSession()

    session.workflow_state = (
        OfferWorkflowState.WAITING_FOR_SALESPERSON
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.WAITING_FOR_SALESPERSON
    )
