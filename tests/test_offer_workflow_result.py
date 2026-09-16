from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)

from app.agent.offers.offer_workflow_result import (
    OfferWorkflowResult,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


def create_agent_result() -> OfferAgentResult:

    context = OfferContext(
        raw_request=(
            "Potrzebuję okno 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    return OfferAgentResult(
        context=context,
        validation=validation,
        is_ready_for_pricing=True,
        requires_salesperson_input=False,
    )


def test_workflow_result_stores_session():

    session = OfferAgentSession()

    result = OfferWorkflowResult(
        session=session,
        agent_result=create_agent_result(),
    )

    assert result.session is session


def test_workflow_result_stores_agent_result():

    agent_result = create_agent_result()

    result = OfferWorkflowResult(
        session=OfferAgentSession(),
        agent_result=agent_result,
    )

    assert (
        result.agent_result
        is agent_result
    )


def test_workflow_result_exposes_current_context():

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=1200,
        height=1500,
    )

    session = OfferAgentSession(
        current_context=context,
    )

    result = OfferWorkflowResult(
        session=session,
        agent_result=create_agent_result(),
    )

    assert (
        result.current_context
        == context
    )


def test_workflow_result_exposes_workflow_state():

    session = OfferAgentSession(
        workflow_state=(
            OfferWorkflowState.READY_FOR_PRICING
        ),
    )

    result = OfferWorkflowResult(
        session=session,
        agent_result=create_agent_result(),
    )

    assert (
        result.workflow_state
        == OfferWorkflowState.READY_FOR_PRICING
    )


def test_workflow_result_exposes_questions():

    agent_result = OfferAgentResult(
        context=OfferContext(
            raw_request="test",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=False,
                missing_fields=(
                    "width",
                ),
            )
        ),
        questions=(
            "Podaj proszę szerokość.",
        ),
        requires_salesperson_input=True,
    )

    result = OfferWorkflowResult(
        session=OfferAgentSession(),
        agent_result=agent_result,
    )

    assert result.questions == (
        "Podaj proszę szerokość.",
    )


def test_workflow_result_exposes_messages():

    agent_result = OfferAgentResult(
        context=OfferContext(
            raw_request="test",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=False,
            )
        ),
        messages=(
            "Nie udało się poprawnie "
            "zweryfikować danych.",
        ),
        requires_salesperson_input=True,
    )

    result = OfferWorkflowResult(
        session=OfferAgentSession(),
        agent_result=agent_result,
    )

    assert result.messages == (
        "Nie udało się poprawnie "
        "zweryfikować danych.",
    )


def test_workflow_result_exposes_pricing_status():

    result = OfferWorkflowResult(
        session=OfferAgentSession(),
        agent_result=create_agent_result(),
    )

    assert (
        result.is_ready_for_pricing
        is True
    )

    assert (
        result.requires_salesperson_input
        is False
    )


def test_workflow_result_stores_action():

    result = OfferWorkflowResult(
        session=OfferAgentSession(),
        agent_result=create_agent_result(),
        action=OfferWorkflowAction.CONFIRM_FOR_PRICING,
    )

    assert (
        result.action
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )
