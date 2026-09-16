from dataclasses import dataclass

from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)


@dataclass(frozen=True)
class OfferWorkflowResult:
    """
    Result of processing one step of the offer workflow.

    The result exposes the current session together
    with the latest agent processing result and the
    next workflow action.
    """

    session: OfferAgentSession

    agent_result: OfferAgentResult

    action: OfferWorkflowAction = (
        OfferWorkflowAction.CONTINUE
    )

    @property
    def current_context(self):
        """
        Return the current normalized offer context.
        """

        return self.session.current_context

    @property
    def workflow_state(self):
        """
        Return the current workflow state.
        """

        return self.session.workflow_state

    @property
    def context(self):
        """
        Return the latest offer context.
        """

        return self.agent_result.context

    @property
    def validation(self):
        """
        Return the latest validation result.
        """

        return self.agent_result.validation

    @property
    def questions(self):
        """
        Return questions for the salesperson.
        """

        return self.agent_result.questions

    @property
    def messages(self):
        """
        Return messages for the salesperson.
        """

        return self.agent_result.messages

    @property
    def is_ready_for_pricing(self):
        """
        Return whether the offer is ready for pricing.
        """

        return (
            self.agent_result
            .is_ready_for_pricing
        )

    @property
    def requires_salesperson_input(self):
        """
        Return whether salesperson input is required.
        """

        return (
            self.agent_result
            .requires_salesperson_input
        )
