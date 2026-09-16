from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)


def test_workflow_action_has_continue_value():

    assert (
        OfferWorkflowAction.CONTINUE.value
        == "continue"
    )


def test_workflow_action_has_provide_information_value():

    assert (
        OfferWorkflowAction.PROVIDE_INFORMATION.value
        == "provide_information"
    )


def test_workflow_action_has_confirm_for_pricing_value():

    assert (
        OfferWorkflowAction.CONFIRM_FOR_PRICING.value
        == "confirm_for_pricing"
    )


def test_workflow_action_has_reset_value():

    assert (
        OfferWorkflowAction.RESET.value
        == "reset"
    )


def test_workflow_action_contains_expected_actions():

    assert tuple(
        OfferWorkflowAction
    ) == (
        OfferWorkflowAction.CONTINUE,
        OfferWorkflowAction.PROVIDE_INFORMATION,
        OfferWorkflowAction.CONFIRM_FOR_PRICING,
        OfferWorkflowAction.RESET,
    )
