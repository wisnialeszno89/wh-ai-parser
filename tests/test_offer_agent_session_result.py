from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_agent_session_result import (
    OfferAgentSessionResult,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


def test_session_result_stores_session():

    session = OfferAgentSession()

    result = OfferAgentSessionResult(
        session=session,
        agent_result=OfferAgentResult(
            context=OfferContext(
                raw_request="test",
            ),
            validation=(
                OfferContextValidationResult(
                    is_valid=False,
                )
            ),
        ),
    )

    assert result.session == session


def test_session_result_stores_agent_result():

    agent_result = OfferAgentResult(
        context=OfferContext(
            raw_request="test",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=False,
            )
        ),
    )

    result = OfferAgentSessionResult(
        session=OfferAgentSession(),
        agent_result=agent_result,
    )

    assert result.agent_result == agent_result


def test_session_result_reports_current_context():

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

    result = OfferAgentSessionResult(
        session=session,
        agent_result=OfferAgentResult(
            context=context,
            validation=(
                OfferContextValidationResult(
                    is_valid=True,
                )
            ),
            is_ready_for_pricing=True,
        ),
    )

    assert result.current_context == context


def test_session_result_reports_pricing_readiness():

    context = OfferContext(
        raw_request="test",
    )

    result = OfferAgentSessionResult(
        session=OfferAgentSession(
            current_context=context,
        ),
        agent_result=OfferAgentResult(
            context=context,
            validation=(
                OfferContextValidationResult(
                    is_valid=True,
                )
            ),
            is_ready_for_pricing=True,
        ),
    )

    assert result.is_ready_for_pricing is True


def test_session_result_reports_salesperson_input_requirement():

    context = OfferContext(
        raw_request="test",
    )

    result = OfferAgentSessionResult(
        session=OfferAgentSession(
            current_context=context,
        ),
        agent_result=OfferAgentResult(
            context=context,
            validation=(
                OfferContextValidationResult(
                    is_valid=False,
                    missing_fields=(
                        "width",
                    ),
                )
            ),
            requires_salesperson_input=True,
        ),
    )

    assert (
        result.requires_salesperson_input
        is True
    )


def test_session_result_exposes_questions():

    context = OfferContext(
        raw_request="test",
    )

    result = OfferAgentSessionResult(
        session=OfferAgentSession(
            current_context=context,
        ),
        agent_result=OfferAgentResult(
            context=context,
            validation=(
                OfferContextValidationResult(
                    is_valid=False,
                )
            ),
            questions=(
                "Podaj proszę szerokość.",
            ),
        ),
    )

    assert result.questions == (
        "Podaj proszę szerokość.",
    )


def test_session_result_exposes_messages():

    context = OfferContext(
        raw_request="test",
    )

    result = OfferAgentSessionResult(
        session=OfferAgentSession(
            current_context=context,
        ),
        agent_result=OfferAgentResult(
            context=context,
            validation=(
                OfferContextValidationResult(
                    is_valid=False,
                )
            ),
            messages=(
                "Wykryto nieprawidłowe dane.",
            ),
        ),
    )

    assert result.messages == (
        "Wykryto nieprawidłowe dane.",
    )
