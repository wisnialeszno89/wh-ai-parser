import pytest

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

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)

from app.agent.offers.offer_workflow_result import (
    OfferWorkflowResult,
)

from app.agent.offers.offer_workflow_action import (
    OfferWorkflowAction,
)

from app.agent.offers.offer_workflow_action_resolver import (
    OfferWorkflowActionResolver,
)

from app.agent.offers.offer_workflow_service import (
    OfferWorkflowService,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


@pytest.fixture
def service() -> OfferWorkflowService:

    return OfferWorkflowService()


def create_session_result(
    session: OfferAgentSession,
    *,
    is_ready_for_pricing: bool = False,
    requires_salesperson_input: bool = True,
) -> OfferAgentSessionResult:

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=1200,
        height=1500,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=is_ready_for_pricing,
        )
    )

    agent_result = OfferAgentResult(
        context=context,
        validation=validation,
        is_ready_for_pricing=(
            is_ready_for_pricing
        ),
        requires_salesperson_input=(
            requires_salesperson_input
        ),
    )

    session.current_context = context

    session.workflow_state = (
        OfferWorkflowState.READY_FOR_PRICING
        if is_ready_for_pricing
        else OfferWorkflowState.WAITING_FOR_SALESPERSON
    )

    return OfferAgentSessionResult(
        session=session,
        agent_result=agent_result,
    )


def test_workflow_service_processes_salesperson_message(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert result.session is session


def test_workflow_service_returns_workflow_result(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert isinstance(
        result,
        OfferWorkflowResult,
    )


def test_workflow_service_updates_session_context(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        session.current_context
        is not None
    )

    assert (
        session.current_context.product_type
        == "window"
    )


def test_workflow_service_updates_workflow_state_when_ready(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.READY_FOR_PRICING
    )


def test_workflow_service_updates_workflow_state_when_input_required(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    service.process(
        session,
        "Potrzebuję okno",
    )

    assert (
        session.workflow_state
        == OfferWorkflowState.WAITING_FOR_SALESPERSON
    )


def test_workflow_service_blocks_ambiguous_opening(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500 Dreh-Kipp",
    )

    assert (
        result.workflow_state
        == OfferWorkflowState.WAITING_FOR_SALESPERSON
    )

    assert (
        result.action
        == OfferWorkflowAction.PROVIDE_INFORMATION
    )

    assert (
        result.is_ready_for_pricing
        is False
    )

    assert (
        result.requires_salesperson_input
        is True
    )

    assert (
        result.context.opening
        is None
    )

    assert (
        result.context.conflicts
        == (
            "Ambiguous opening: "
            "opening direction is missing.",
        )
    )


class FakeOfferAgentSessionService:
    """
    Test session service used to verify dependency
    injection and workflow delegation.
    """

    def __init__(
        self,
        result: OfferAgentSessionResult,
    ) -> None:

        self.result = result

        self.received_session = None

        self.received_request = None

    def process(
        self,
        session: OfferAgentSession,
        raw_request: str,
    ) -> OfferAgentSessionResult:

        self.received_session = session

        self.received_request = raw_request

        return self.result


class FakeOfferWorkflowActionResolver:
    """
    Test action resolver used to verify dependency
    injection and workflow action resolution.
    """

    def __init__(
        self,
        action: OfferWorkflowAction,
    ) -> None:

        self.action = action

        self.received_workflow_state = None

    def resolve(
        self,
        workflow_state: OfferWorkflowState,
    ) -> OfferWorkflowAction:

        self.received_workflow_state = (
            workflow_state
        )

        return self.action


def test_workflow_service_uses_injected_session_service():

    session = OfferAgentSession()

    expected_result = (
        create_session_result(
            session,
            is_ready_for_pricing=True,
            requires_salesperson_input=False,
        )
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
    )

    result = service.process(
        session,
        "custom request",
    )

    assert (
        session_service.received_session
        is session
    )

    assert (
        session_service.received_request
        == "custom request"
    )

    assert isinstance(
        result,
        OfferWorkflowResult,
    )

    assert result.session is session

    assert (
        result.agent_result
        is expected_result.agent_result
    )


def test_workflow_service_preserves_multi_message_session(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    first_result = service.process(
        session,
        "Potrzebuję okno",
    )

    assert (
        first_result.requires_salesperson_input
        is True
    )

    second_result = service.process(
        session,
        "1200x1500",
    )

    assert (
        second_result.is_ready_for_pricing
        is True
    )

    assert (
        session.current_context.product_type
        == "window"
    )

    assert (
        session.current_context.width
        == 1200
    )

    assert (
        session.current_context.height
        == 1500
    )


def test_workflow_service_resolves_action_when_ready(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    result = service.process(
        session,
        "Potrzebuję okno 1200x1500",
    )

    assert (
        result.action
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )


def test_workflow_service_resolves_action_when_input_required(
    service: OfferWorkflowService,
):

    session = OfferAgentSession()

    result = service.process(
        session,
        "Potrzebuję okno",
    )

    assert (
        result.action
        == OfferWorkflowAction.PROVIDE_INFORMATION
    )


def test_workflow_service_uses_injected_action_resolver():

    session = OfferAgentSession()

    expected_result = (
        create_session_result(
            session,
            is_ready_for_pricing=True,
            requires_salesperson_input=False,
        )
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    action_resolver = (
        FakeOfferWorkflowActionResolver(
            OfferWorkflowAction.CONFIRM_FOR_PRICING
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
        action_resolver=action_resolver,
    )

    result = service.process(
        session,
        "custom request",
    )

    assert (
        action_resolver.received_workflow_state
        == OfferWorkflowState.READY_FOR_PRICING
    )

    assert (
        result.action
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )


def test_workflow_service_resolves_continue_when_pricing():

    session = OfferAgentSession()

    expected_result = (
        create_session_result(
            session,
            is_ready_for_pricing=True,
            requires_salesperson_input=False,
        )
    )

    session.workflow_state = (
        OfferWorkflowState.PRICING
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
    )

    result = service.process(
        session,
        "continue pricing",
    )

    assert (
        result.action
        == OfferWorkflowAction.CONTINUE
    )


def test_workflow_service_resolves_continue_when_completed():

    session = OfferAgentSession()

    expected_result = (
        create_session_result(
            session,
            is_ready_for_pricing=True,
            requires_salesperson_input=False,
        )
    )

    session.workflow_state = (
        OfferWorkflowState.COMPLETED
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
    )

    result = service.process(
        session,
        "workflow completed",
    )

    assert (
        result.action
        == OfferWorkflowAction.CONTINUE
    )


def test_workflow_service_resolves_reset_when_failed():

    session = OfferAgentSession()

    expected_result = (
        create_session_result(
            session,
            is_ready_for_pricing=False,
            requires_salesperson_input=True,
        )
    )

    session.workflow_state = (
        OfferWorkflowState.FAILED
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
    )

    result = service.process(
        session,
        "workflow failed",
    )

    assert (
        result.action
        == OfferWorkflowAction.RESET
    )


def test_workflow_service_resolves_action_from_result_session():

    original_session = OfferAgentSession(
        workflow_state=(
            OfferWorkflowState.WAITING_FOR_SALESPERSON
        )
    )

    result_session = OfferAgentSession(
        workflow_state=(
            OfferWorkflowState.READY_FOR_PRICING
        )
    )

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=1200,
        height=1500,
    )

    agent_result = OfferAgentResult(
        context=context,
        validation=(
            OfferContextValidationResult(
                is_valid=True,
            )
        ),
        is_ready_for_pricing=True,
        requires_salesperson_input=False,
    )

    expected_result = OfferAgentSessionResult(
        session=result_session,
        agent_result=agent_result,
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
    )

    result = service.process(
        original_session,
        "1200x1500",
    )

    assert (
        result.session
        is result_session
    )

    assert (
        result.action
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )


def test_workflow_service_passes_result_workflow_state_to_resolver():

    original_session = OfferAgentSession(
        workflow_state=(
            OfferWorkflowState.WAITING_FOR_SALESPERSON
        )
    )

    result_session = OfferAgentSession(
        workflow_state=(
            OfferWorkflowState.READY_FOR_PRICING
        )
    )

    context = OfferContext(
        raw_request="test",
    )

    agent_result = OfferAgentResult(
        context=context,
        validation=(
            OfferContextValidationResult(
                is_valid=True,
            )
        ),
        is_ready_for_pricing=True,
        requires_salesperson_input=False,
    )

    expected_result = OfferAgentSessionResult(
        session=result_session,
        agent_result=agent_result,
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    action_resolver = (
        FakeOfferWorkflowActionResolver(
            OfferWorkflowAction.CONFIRM_FOR_PRICING
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
        action_resolver=action_resolver,
    )

    service.process(
        original_session,
        "1200x1500",
    )

    assert (
        action_resolver.received_workflow_state
        == OfferWorkflowState.READY_FOR_PRICING
    )


class FakeOfferWorkflowActionHandler:
    """
    Test action handler used to verify dependency
    injection and workflow action handling.
    """

    def __init__(
        self,
        handled_action,
    ) -> None:

        self.handled_action = (
            handled_action
        )

        self.received_action = None

    def handle(
        self,
        action,
    ):

        self.received_action = action

        return self.handled_action


def test_workflow_service_uses_injected_action_handler():

    session = OfferAgentSession()

    expected_result = (
        create_session_result(
            session,
            is_ready_for_pricing=True,
            requires_salesperson_input=False,
        )
    )

    session_service = (
        FakeOfferAgentSessionService(
            expected_result
        )
    )

    action_resolver = (
        FakeOfferWorkflowActionResolver(
            OfferWorkflowAction
            .CONFIRM_FOR_PRICING
        )
    )

    action_handler = (
        FakeOfferWorkflowActionHandler(
            OfferWorkflowAction
            .CONFIRM_FOR_PRICING
        )
    )

    service = OfferWorkflowService(
        session_service=session_service,
        action_resolver=action_resolver,
        action_handler=action_handler,
    )

    result = service.process(
        session,
        "custom request",
    )

    assert (
        action_handler.received_action
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )

    assert (
        result.action
        == OfferWorkflowAction.CONFIRM_FOR_PRICING
    )


def test_workflow_service_ready_for_pricing_maps_to_existing_quote_plan():
    from app.agent.agent_request import AgentRequest
    from app.agent.agent_intent import AgentIntent
    from app.agent.planning.agent_planner import AgentPlanner
    from app.agent.offers.offer_agent_session import OfferAgentSession
    from app.agent.offers.offer_workflow_action import OfferWorkflowAction

    session = OfferAgentSession()
    service = OfferWorkflowService()

    result = service.process(
        session,
        "Przygotuj ofertę na okno 1200x1500",
    )

    assert result.action == OfferWorkflowAction.CONFIRM_FOR_PRICING
    assert result.is_ready_for_pricing is True

    planner = AgentPlanner()
    plan = planner.plan(
        AgentRequest(message="Przygotuj ofertę na okno 1200x1500")
    )

    assert plan.intent == AgentIntent.CREATE_QUOTE
    assert len(plan.steps) == 5
    assert plan.steps[-1].action.name == "prepare_quote"
    assert plan.steps[-1].action.requires_confirmation is True
