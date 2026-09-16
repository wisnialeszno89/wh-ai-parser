from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)

from app.agent.offers.offer_workflow_state_resolver import (
    OfferWorkflowStateResolver,
)


def create_agent_result(
    *,
    is_ready_for_pricing: bool,
) -> OfferAgentResult:

    context = OfferContext(
        raw_request="test",
    )

    validation = (
        OfferContextValidationResult(
            is_valid=is_ready_for_pricing,
        )
    )

    return OfferAgentResult(
        context=context,
        validation=validation,
        is_ready_for_pricing=(
            is_ready_for_pricing
        ),
        requires_salesperson_input=(
            not is_ready_for_pricing
        ),
    )


def test_resolver_returns_ready_for_pricing():

    resolver = OfferWorkflowStateResolver()

    result = create_agent_result(
        is_ready_for_pricing=True,
    )

    state = resolver.resolve(
        result
    )

    assert (
        state
        == OfferWorkflowState.READY_FOR_PRICING
    )


def test_resolver_returns_waiting_for_salesperson():

    resolver = OfferWorkflowStateResolver()

    result = create_agent_result(
        is_ready_for_pricing=False,
    )

    state = resolver.resolve(
        result
    )

    assert (
        state
        == OfferWorkflowState.WAITING_FOR_SALESPERSON
    )
