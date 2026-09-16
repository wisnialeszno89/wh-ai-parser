import pytest

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest

from app.agent.execution.wh_action_executor import (
    WHActionExecutor,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


def build_context():

    from app.agent.offers.offer_context import OfferContext

    context = ExecutionContext(
        request=AgentRequest(
            message="Prepare quote"
        )
    )

    context.set_value(
        "offer_context",
        OfferContext(
            raw_request="Prepare quote",
            width=1200,
            height=1500,
            quantity=1,
            product_type="okno",
        ),
    )

    return context


@pytest.mark.parametrize(
    "action_name",
    (
        "analyze_request",
        "collect_offer_context",
        "validate_offer",
        "build_construction",
        "prepare_quote",
    ),
)
def test_wh_executor_supports_wh_actions(
    action_name,
):

    executor = WHActionExecutor()

    action = AgentAction(
        name=action_name,
        description="Test action",
    )

    assert executor.supports(action) is True


def test_wh_executor_rejects_unknown_action():

    executor = WHActionExecutor()

    action = AgentAction(
        name="write_word_document",
        description="Word action",
    )

    assert executor.supports(action) is False


def test_prepare_quote_requires_review():

    executor = WHActionExecutor()

    context = build_context()

    result = executor.execute(
        AgentAction(
            name="prepare_quote",
            description="Prepare quote",
        ),
        context,
    )

    assert result.success is True

    assert result.requires_manual_review is True

    assert (
        context.get_value("quote_prepared")
        is True
    )


def test_build_construction_updates_context():

    executor = WHActionExecutor()

    context = build_context()

    result = executor.execute(
        AgentAction(
            name="build_construction",
            description="Build construction",
        ),
        context,
    )

    assert result.success is True

    assert (
        context.get_value(
            "construction_build_started"
        )
        is True
    )

    assert (
        result.metadata["workflow_stage"]
        == "construction"
    )


def test_collect_offer_context_preserves_real_offer_context():
    from app.agent.agent_request import AgentRequest
    from app.agent.offers.offer_context import OfferContext
    from app.agent.agent_action import AgentAction
    from app.agent.execution.wh_action_executor import WHActionExecutor
    from app.agent.runtime.execution_context import ExecutionContext

    offer_context = OfferContext(
        raw_request="Przygotuj ofertę na okno 1200x1500",
        width=1200,
        height=1500,
        quantity=1,
        product_type="okno",
    )

    context = ExecutionContext(
        request=AgentRequest(
            message=offer_context.raw_request
        )
    )

    context.set_value(
        "offer_context",
        offer_context,
    )

    executor = WHActionExecutor()

    result = executor.execute(
        AgentAction(
            name="collect_offer_context",
            description="Collect offer context.",
        ),
        context,
    )

    assert result.success is True
    assert context.get_value("offer_context") == offer_context
    assert context.get_value("offer_context").width == 1200
    assert context.get_value("offer_context").height == 1500


def test_collect_offer_context_blocks_when_context_is_missing():
    from app.agent.agent_request import AgentRequest
    from app.agent.agent_action import AgentAction
    from app.agent.execution.wh_action_executor import WHActionExecutor
    from app.agent.runtime.execution_context import ExecutionContext

    context = ExecutionContext(
        request=AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    executor = WHActionExecutor()

    result = executor.execute(
        AgentAction(
            name="collect_offer_context",
            description="Collect offer context.",
        ),
        context,
    )

    assert result.success is False
    assert result.requires_manual_review is True


def test_build_construction_blocks_when_offer_context_is_missing():
    from app.agent.agent_request import AgentRequest
    from app.agent.agent_action import AgentAction
    from app.agent.execution.wh_action_executor import WHActionExecutor
    from app.agent.runtime.execution_context import ExecutionContext

    context = ExecutionContext(
        request=AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    executor = WHActionExecutor()

    result = executor.execute(
        AgentAction(
            name="build_construction",
            description="Build construction.",
        ),
        context,
    )

    assert result.success is False
    assert result.requires_manual_review is True


def test_build_construction_resolves_known_opening():
    from app.agent.offers.offer_context import OfferContext

    executor = WHActionExecutor()

    context = ExecutionContext(
        request=AgentRequest(
            message="Potrzebuję okno 1200x1500 DKR"
        )
    )

    context.set_value(
        "offer_context",
        OfferContext(
            raw_request="Potrzebuję okno 1200x1500 DKR",
            width=1200,
            height=1500,
            quantity=1,
            product_type="window",
            opening="RIGHT_TILT_TURN",
        ),
    )

    result = executor.execute(
        AgentAction(
            name="build_construction",
            description="Build construction.",
        ),
        context,
    )

    assert result.success is True

    construction_definition = context.get_value(
        "construction_definition"
    )

    assert construction_definition is not None
    assert (
        construction_definition.code
        == "SINGLE_RIGHT_TILT_TURN"
    )
