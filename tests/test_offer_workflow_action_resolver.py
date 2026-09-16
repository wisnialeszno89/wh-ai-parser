from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)

from app.agent.offers.offer_workflow_action_resolver import (
    OfferWorkflowActionResolver,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


def test_resolver_returns_collect_information_for_new_state():

    resolver = OfferWorkflowActionResolver()

    result = resolver.resolve(
        OfferWorkflowState.NEW
    )

    assert (
        result
        == OfferWorkflowAction.CONTINUE
    )


def test_resolver_returns_ask_salesperson_when_waiting():

    resolver = OfferWorkflowActionResolver()

    result = resolver.resolve(
        OfferWorkflowState.WAITING_FOR_SALESPERSON
    )

    assert (
        result
        == OfferWorkflowAction.PROVIDE_INFORMATION
    )


def test_resolver_returns_start_pricing_when_ready():

    resolver = OfferWorkflowActionResolver()

    result = resolver.resolve(
        OfferWorkflowState.READY_FOR_PRICING
    )

    assert (
        result
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )


def test_resolver_returns_continue_when_pricing():

    resolver = OfferWorkflowActionResolver()

    result = resolver.resolve(
        OfferWorkflowState.PRICING
    )

    assert (
        result
        == OfferWorkflowAction.CONTINUE
    )


def test_resolver_returns_continue_when_completed():

    resolver = OfferWorkflowActionResolver()

    result = resolver.resolve(
        OfferWorkflowState.COMPLETED
    )

    assert (
        result
        == OfferWorkflowAction.CONTINUE
    )


def test_resolver_returns_reset_when_failed():

    resolver = OfferWorkflowActionResolver()

    result = resolver.resolve(
        OfferWorkflowState.FAILED
    )

    assert (
        result
        == OfferWorkflowAction.RESET
    )
