from app.agent.offers.offer_workflow_action import OfferWorkflowAction
from app.agent.offers.offer_workflow_action_handler import OfferWorkflowActionHandler


def test_confirm_for_pricing_returns_explicit_execution_intent():
    handler = OfferWorkflowActionHandler()

    result = handler.handle(OfferWorkflowAction.CONFIRM_FOR_PRICING)

    assert result == OfferWorkflowAction.CONFIRM_FOR_PRICING
