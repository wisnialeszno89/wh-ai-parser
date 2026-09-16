from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


class OfferWorkflowActionResolver:
    """
    Resolve the next workflow action based on the
    current offer workflow state.
    """

    def resolve(
        self,
        workflow_state: OfferWorkflowState,
    ) -> OfferWorkflowAction:
        """
        Determine the next action for the current
        workflow state.
        """

        if (
            workflow_state
            == OfferWorkflowState.NEW
        ):
            return OfferWorkflowAction.CONTINUE

        if (
            workflow_state
            == OfferWorkflowState.COLLECTING_INFORMATION
        ):
            return OfferWorkflowAction.CONTINUE

        if (
            workflow_state
            == OfferWorkflowState.WAITING_FOR_SALESPERSON
        ):
            return (
                OfferWorkflowAction
                .PROVIDE_INFORMATION
            )

        if (
            workflow_state
            == OfferWorkflowState.READY_FOR_PRICING
        ):
            return (
                OfferWorkflowAction
                .CONFIRM_FOR_PRICING
            )

        if (
            workflow_state
            == OfferWorkflowState.PRICING
        ):
            return OfferWorkflowAction.CONTINUE

        if (
            workflow_state
            == OfferWorkflowState.COMPLETED
        ):
            return OfferWorkflowAction.CONTINUE

        if (
            workflow_state
            == OfferWorkflowState.FAILED
        ):
            return OfferWorkflowAction.RESET

        raise ValueError(
            "Unsupported offer workflow state: "
            f"{workflow_state}"
        )
