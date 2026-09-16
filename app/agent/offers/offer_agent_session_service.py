from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_agent_service import (
    OfferAgentService,
)

from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_agent_session_result import (
    OfferAgentSessionResult,
)

from app.agent.offers.offer_context_merger import (
    OfferContextMerger,
)

from app.agent.offers.offer_context_question_builder import (
    OfferContextQuestionBuilder,
)

from app.agent.offers.offer_context_validator import (
    OfferContextValidator,
)

from app.agent.offers.offer_workflow_state_resolver import (
    OfferWorkflowStateResolver,
)


class OfferAgentSessionService:
    """
    Coordinate a multi-message offer workflow.

    The service keeps the current offer context and
    workflow state inside an OfferAgentSession while
    the salesperson provides additional information
    over multiple messages.

    The salesperson remains the source of commercial
    decisions. This service only accumulates,
    validates and structures the provided information.
    """

    def __init__(
        self,
        offer_agent_service: (
            OfferAgentService | None
        ) = None,
        context_merger: (
            OfferContextMerger | None
        ) = None,
        context_validator: (
            OfferContextValidator | None
        ) = None,
        question_builder: (
            OfferContextQuestionBuilder | None
        ) = None,
        workflow_state_resolver: (
            OfferWorkflowStateResolver | None
        ) = None,
    ) -> None:

        self.offer_agent_service = (
            offer_agent_service
            if offer_agent_service is not None
            else OfferAgentService()
        )

        self.context_merger = (
            context_merger
            if context_merger is not None
            else OfferContextMerger()
        )

        self.context_validator = (
            context_validator
            if context_validator is not None
            else OfferContextValidator()
        )

        self.question_builder = (
            question_builder
            if question_builder is not None
            else OfferContextQuestionBuilder()
        )

        self.workflow_state_resolver = (
            workflow_state_resolver
            if workflow_state_resolver is not None
            else OfferWorkflowStateResolver()
        )

    def process(
        self,
        session: OfferAgentSession,
        raw_request: str,
    ) -> OfferAgentSessionResult:
        """
        Process one salesperson message within an
        existing offer session.
        """

        agent_result = (
            self.offer_agent_service.process(
                raw_request
            )
        )

        if (
            session.current_context is None
        ):

            session.current_context = (
                agent_result.context
            )

            session.workflow_state = (
                self.workflow_state_resolver.resolve(
                    agent_result
                )
            )

            return OfferAgentSessionResult(
                session=session,
                agent_result=agent_result,
            )

        merged_context = (
            self.context_merger.merge(
                session.current_context,
                agent_result.context,
            )
        )

        validation = (
            self.context_validator.validate(
                merged_context
            )
        )

        question_result = (
            self.question_builder.build(
                validation
            )
        )

        is_ready_for_pricing = (
            validation.is_valid
        )

        merged_agent_result = (
            OfferAgentResult(
                context=merged_context,
                validation=validation,
                questions=(
                    question_result.questions
                ),
                messages=(
                    question_result.messages
                ),
                is_ready_for_pricing=(
                    is_ready_for_pricing
                ),
                requires_salesperson_input=(
                    not is_ready_for_pricing
                ),
            )
        )

        session.current_context = (
            merged_context
        )

        session.workflow_state = (
            self.workflow_state_resolver.resolve(
                merged_agent_result
            )
        )

        return OfferAgentSessionResult(
            session=session,
            agent_result=merged_agent_result,
        )
