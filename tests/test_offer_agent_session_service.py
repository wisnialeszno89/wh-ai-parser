from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)


from app.agent.offers.offer_agent_session_result import (
    OfferAgentSessionResult,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_merger import (
    OfferContextMerger,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)

from app.agent.offers.offer_agent_session_service import (
    OfferAgentSessionService,
)
from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)

from app.agent.offers.offer_workflow_state_resolver import (
    OfferWorkflowStateResolver,
)

class FakeOfferAgentService:
    """
    Fake offer agent service used to verify session
    processing behavior.
    """

    def __init__(
        self,
        result: OfferAgentResult,
    ) -> None:

        self.result = result

        self.received_request = None

    def process(
        self,
        raw_request: str,
    ) -> OfferAgentResult:

        self.received_request = raw_request

        return self.result


class FakeOfferContextMerger:
    """
    Fake context merger used to verify that the
    session service merges existing and newly
    extracted contexts.
    """

    def __init__(
        self,
        result: OfferContext,
    ) -> None:

        self.result = result

        self.received_existing = None

        self.received_update = None

    def merge(
        self,
        existing: OfferContext,
        update: OfferContext,
    ) -> OfferContext:

        self.received_existing = existing

        self.received_update = update

        return self.result


class FakeOfferContextValidator:
    """
    Fake validator used to verify that merged
    session context is validated again.
    """

    def __init__(
        self,
        result: OfferContextValidationResult,
    ) -> None:

        self.result = result

        self.received_context = None

    def validate(
        self,
        context: OfferContext,
    ) -> OfferContextValidationResult:

        self.received_context = context

        return self.result


def create_agent_result(
    context: OfferContext,
    validation: (
        OfferContextValidationResult | None
    ) = None,
) -> OfferAgentResult:

    if validation is None:

        validation = (
            OfferContextValidationResult(
                is_valid=True,
            )
        )

    return OfferAgentResult(
        context=context,
        validation=validation,
        is_ready_for_pricing=(
            validation.is_valid
        ),
        requires_salesperson_input=(
            not validation.is_valid
        ),
    )


def test_session_service_stores_first_context():

    context = OfferContext(
        raw_request=(
            "Potrzebuję okno 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
    )

    result = create_agent_result(
        context
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                result
            )
        )
    )

    session = OfferAgentSession()

    session_result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        session.current_context
        == context
    )

    assert (
        session_result.context
        == context
    )


def test_session_service_passes_request_to_agent_service():

    context = OfferContext(
        raw_request="test",
    )

    agent_service = (
        FakeOfferAgentService(
            create_agent_result(
                context
            )
        )
    )

    service = OfferAgentSessionService(
        offer_agent_service=agent_service,
    )

    session = OfferAgentSession()

    service.process(
        session,
        "custom request",
    )

    assert (
        agent_service.received_request
        == "custom request"
    )


def test_session_service_does_not_merge_first_context():

    context = OfferContext(
        raw_request="Okno 1200x1500",
        product_type="window",
        width=1200,
        height=1500,
    )

    merger = FakeOfferContextMerger(
        context
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                create_agent_result(
                    context
                )
            )
        ),
        context_merger=merger,
    )

    session = OfferAgentSession()

    service.process(
        session,
        "Okno 1200x1500",
    )

    assert (
        merger.received_existing
        is None
    )

    assert (
        merger.received_update
        is None
    )


def test_session_service_merges_new_context():

    existing = OfferContext(
        raw_request=(
            "Potrzebuję 3 okna 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
        quantity=3,
    )

    update = OfferContext(
        raw_request=(
            "antracyt z zewnątrz"
        ),
        color_outside="anthracite",
    )

    merged = OfferContext(
        raw_request=(
            "Potrzebuję 3 okna 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
        quantity=3,
        color_outside="anthracite",
    )

    merger = FakeOfferContextMerger(
        merged
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                create_agent_result(
                    update
                )
            )
        ),
        context_merger=merger,
    )

    session = OfferAgentSession(
        current_context=existing,
    )

    service.process(
        session,
        "antracyt z zewnątrz",
    )

    assert (
        merger.received_existing
        == existing
    )

    assert (
        merger.received_update
        == update
    )

    assert (
        session.current_context
        == merged
    )


def test_session_service_validates_merged_context():

    existing = OfferContext(
        raw_request="okno",
        product_type="window",
    )

    update = OfferContext(
        raw_request="1200x1500",
        width=1200,
        height=1500,
    )

    merged = OfferContext(
        raw_request="okno",
        product_type="window",
        width=1200,
        height=1500,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    validator = (
        FakeOfferContextValidator(
            validation
        )
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                create_agent_result(
                    update
                )
            )
        ),
        context_merger=(
            FakeOfferContextMerger(
                merged
            )
        ),
        context_validator=validator,
    )

    session = OfferAgentSession(
        current_context=existing,
    )

    service.process(
        session,
        "1200x1500",
    )

    assert (
        validator.received_context
        == merged
    )


def test_session_service_returns_merged_validation():

    existing = OfferContext(
        raw_request="okno",
        product_type="window",
    )

    update = OfferContext(
        raw_request="1200x1500",
        width=1200,
        height=1500,
    )

    merged = OfferContext(
        raw_request="okno",
        product_type="window",
        width=1200,
        height=1500,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                create_agent_result(
                    update
                )
            )
        ),
        context_merger=(
            FakeOfferContextMerger(
                merged
            )
        ),
        context_validator=(
            FakeOfferContextValidator(
                validation
            )
        ),
    )

    session = OfferAgentSession(
        current_context=existing,
    )

    result = service.process(
        session,
        "1200x1500",
    )

    assert (
        result.validation
        == validation
    )


def test_session_service_is_ready_after_context_becomes_complete():

    existing = OfferContext(
        raw_request="Potrzebuję okno",
        product_type="window",
    )

    update = OfferContext(
        raw_request="1200x1500",
        width=1200,
        height=1500,
    )

    merged = OfferContext(
        raw_request="Potrzebuję okno",
        product_type="window",
        width=1200,
        height=1500,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                create_agent_result(
                    update
                )
            )
        ),
        context_merger=(
            FakeOfferContextMerger(
                merged
            )
        ),
        context_validator=(
            FakeOfferContextValidator(
                validation
            )
        ),
    )

    session = OfferAgentSession(
        current_context=existing,
    )

    result = service.process(
        session,
        "1200x1500",
    )

    assert (
        result.is_ready_for_pricing
        is True
    )

    assert (
        result.requires_salesperson_input
        is False
    )


def test_session_service_requires_input_when_merged_context_invalid():

    existing = OfferContext(
        raw_request="okno",
        product_type="window",
    )

    update = OfferContext(
        raw_request="1200",
        width=1200,
    )

    merged = OfferContext(
        raw_request="okno",
        product_type="window",
        width=1200,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            missing_fields=(
                "height",
            ),
        )
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                create_agent_result(
                    update,
                    validation,
                )
            )
        ),
        context_merger=(
            FakeOfferContextMerger(
                merged
            )
        ),
        context_validator=(
            FakeOfferContextValidator(
                validation
            )
        ),
    )

    session = OfferAgentSession(
        current_context=existing,
    )

    result = service.process(
        session,
        "1200",
    )

    assert (
        result.is_ready_for_pricing
        is False
    )

    assert (
        result.requires_salesperson_input
        is True
    )


def test_session_service_returns_session_result():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert isinstance(
        result,
        OfferAgentSessionResult,
    )


def test_session_service_result_contains_session():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert result.session is session


def test_session_service_result_contains_agent_result():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert isinstance(
        result.agent_result,
        OfferAgentResult,
    )


def test_session_service_result_exposes_current_context():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        result.current_context
        == session.current_context
    )


def test_session_service_result_exposes_pricing_readiness():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        result.is_ready_for_pricing
        is True
    )


def test_session_service_result_exposes_questions():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    result = service.process(
        session,
        "Potrzebuję okno",
    )

    assert (
        "Podaj proszę szerokość."
        in result.questions
    )

    assert (
        "Podaj proszę wysokość."
        in result.questions
    )



class FakeOfferWorkflowStateResolver:
    """
    Test workflow state resolver used to verify
    dependency injection.
    """

    def __init__(
        self,
        state: OfferWorkflowState,
    ) -> None:

        self.state = state

        self.received_result = None

    def resolve(
        self,
        result: OfferAgentResult,
    ) -> OfferWorkflowState:

        self.received_result = result

        return self.state


def test_session_service_updates_workflow_state_when_ready():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.READY_FOR_PRICING
    )


def test_session_service_updates_workflow_state_when_input_required():

    session = OfferAgentSession()

    service = OfferAgentSessionService()

    service.process(
        session,
        "Potrzebuję okno",
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.WAITING_FOR_SALESPERSON
    )


def test_session_service_uses_injected_workflow_state_resolver():

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=1200,
        height=1500,
    )

    agent_result = create_agent_result(
        context
    )

    resolver = (
        FakeOfferWorkflowStateResolver(
            OfferWorkflowState.COLLECTING_INFORMATION
        )
    )

    service = OfferAgentSessionService(
        offer_agent_service=(
            FakeOfferAgentService(
                agent_result
            )
        ),
        workflow_state_resolver=resolver,
    )

    session = OfferAgentSession()

    service.process(
        session,
        "test",
    )

    assert (
        resolver.received_result
        == agent_result
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.COLLECTING_INFORMATION
    )
