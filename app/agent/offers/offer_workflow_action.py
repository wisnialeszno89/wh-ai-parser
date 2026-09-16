from enum import Enum


class OfferWorkflowAction(
    str,
    Enum,
):
    """
    Explicit action requested by the salesperson
    within the offer workflow.
    """

    CONTINUE = "continue"

    PROVIDE_INFORMATION = (
        "provide_information"
    )

    CONFIRM_FOR_PRICING = (
        "confirm_for_pricing"
    )

    RESET = "reset"
