from app.agent.agent_intent import AgentIntent
from app.agent.capabilities.capability_router import (
    CapabilityRouter,
)
from app.agent.capabilities.default_capabilities import (
    create_default_capability_registry,
)


def create_router() -> CapabilityRouter:
    registry = (
        create_default_capability_registry()
    )

    return CapabilityRouter(registry)


def test_quote_intent_routes_to_wh_window():
    capability = (
        create_router().resolve(
            AgentIntent.CREATE_QUOTE
        )
    )

    assert capability is not None
    assert capability.name == "WH_WINDOW"


def test_modify_quote_routes_to_wh_window():
    capability = (
        create_router().resolve(
            AgentIntent.MODIFY_QUOTE
        )
    )

    assert capability is not None
    assert capability.name == "WH_WINDOW"


def test_customer_reply_routes_to_word():
    capability = (
        create_router().resolve(
            AgentIntent.WRITE_CUSTOMER_REPLY
        )
    )

    assert capability is not None
    assert capability.name == "WORD"


def test_unknown_intent_returns_none():
    capability = (
        create_router().resolve(
            AgentIntent.UNKNOWN
        )
    )

    assert capability is None


def test_unmapped_intent_returns_none():
    capability = (
        create_router().resolve(
            AgentIntent.CHECK_MARKET
        )
    )

    assert capability is None
