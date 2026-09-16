from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)

from app.agent.offers.offer_workflow_result import (
    OfferWorkflowResult,
)


class OfferWorkflowActionHandler:
    """
    Handle actions produced by the offer workflow.
    """

    def handle(
        self,
        action: (
            OfferWorkflowAction
            | OfferWorkflowResult
        ),
    ) -> OfferWorkflowAction:
        """
        Handle a workflow action or workflow result.
        """

        if isinstance(
            action,
            OfferWorkflowResult,
        ):
            action = action.action

        if (
            action
            == OfferWorkflowAction.CONTINUE
        ):
            return action

        if (
            action
            == OfferWorkflowAction.PROVIDE_INFORMATION
        ):
            return action

        if (
            action
            == OfferWorkflowAction.CONFIRM_FOR_PRICING
        ):
            return action

        if (
            action
            == OfferWorkflowAction.RESET
        ):
            return action

        raise ValueError(
            "Unsupported offer workflow action: "
            f"{action}"
        )
