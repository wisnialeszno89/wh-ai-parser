from dataclasses import dataclass

from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


@dataclass(frozen=True)
class OfferAgentSessionResult:
    """
    Result of processing one message within an
    offer agent session.

    The result exposes both the updated session and
    the result produced by the offer agent workflow.

    It provides a session-level interface for callers
    such as Navimind while keeping the underlying
    agent result available.
    """

    session: OfferAgentSession

    agent_result: OfferAgentResult

    @property
    def context(
        self,
    ) -> OfferContext:
        """
        Return the offer context produced by the
        current agent workflow.
        """

        return self.agent_result.context

    @property
    def validation(
        self,
    ) -> OfferContextValidationResult:
        """
        Return the validation result produced by the
        current agent workflow.
        """

        return self.agent_result.validation

    @property
    def current_context(
        self,
    ) -> OfferContext | None:
        """
        Return the current context stored in the
        session.
        """

        return self.session.current_context

    @property
    def is_ready_for_pricing(
        self,
    ) -> bool:
        """
        Return whether the current offer context is
        ready for the pricing stage.
        """

        return (
            self.agent_result
            .is_ready_for_pricing
        )

    @property
    def requires_salesperson_input(
        self,
    ) -> bool:
        """
        Return whether additional salesperson input
        is required.
        """

        return (
            self.agent_result
            .requires_salesperson_input
        )

    @property
    def questions(
        self,
    ) -> tuple[str, ...]:
        """
        Return questions generated for the
        salesperson.
        """

        return self.agent_result.questions

    @property
    def messages(
        self,
    ) -> tuple[str, ...]:
        """
        Return validation or workflow messages.
        """

        return self.agent_result.messages
