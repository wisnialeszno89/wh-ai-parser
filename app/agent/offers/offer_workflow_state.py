from enum import Enum


class OfferWorkflowState(
    str,
    Enum,
):
    """
    Represent the current state of the offer
    workflow.
    """

    NEW = "new"

    COLLECTING_INFORMATION = (
        "collecting_information"
    )

    WAITING_FOR_SALESPERSON = (
        "waiting_for_salesperson"
    )

    READY_FOR_PRICING = (
        "ready_for_pricing"
    )

    PRICING = "pricing"

    COMPLETED = "completed"

    FAILED = "failed"
