from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


def test_workflow_state_contains_new():

    assert (
        OfferWorkflowState.NEW.value
        == "new"
    )


def test_workflow_state_contains_collecting_information():

    assert (
        OfferWorkflowState.COLLECTING_INFORMATION.value
        == "collecting_information"
    )


def test_workflow_state_contains_waiting_for_salesperson():

    assert (
        OfferWorkflowState.WAITING_FOR_SALESPERSON.value
        == "waiting_for_salesperson"
    )


def test_workflow_state_contains_ready_for_pricing():

    assert (
        OfferWorkflowState.READY_FOR_PRICING.value
        == "ready_for_pricing"
    )


def test_workflow_state_contains_pricing():

    assert (
        OfferWorkflowState.PRICING.value
        == "pricing"
    )


def test_workflow_state_contains_completed():

    assert (
        OfferWorkflowState.COMPLETED.value
        == "completed"
    )


def test_workflow_state_contains_failed():

    assert (
        OfferWorkflowState.FAILED.value
        == "failed"
    )
