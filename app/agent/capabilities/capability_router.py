from app.agent.agent_intent import AgentIntent
from app.agent.capabilities.capability import Capability
from app.agent.capabilities.capability_registry import (
    CapabilityRegistry,
)


class CapabilityRouter:
    """
    Maps semantic agent intents to available capabilities.

    The router does not execute anything.
    It only answers which area of competence should
    handle a given intent.
    """

    INTENT_CAPABILITY_MAP = {
        AgentIntent.CREATE_QUOTE: "WH_WINDOW",
        AgentIntent.MODIFY_QUOTE: "WH_WINDOW",
        AgentIntent.CHECK_TECHNICAL: "WH_WINDOW",
        AgentIntent.COMPARE_VARIANTS: "WH_WINDOW",
        AgentIntent.EXECUTE_IN_WH: "WH_WINDOW",
        AgentIntent.OBSERVE_WORKFLOW: "WH_WINDOW",
        AgentIntent.WRITE_CUSTOMER_REPLY: "WORD",
    }

    def __init__(
        self,
        registry: CapabilityRegistry,
    ) -> None:
        self.registry = registry

    def resolve(
        self,
        intent: AgentIntent,
    ) -> Capability | None:
        capability_name = (
            self.INTENT_CAPABILITY_MAP.get(intent)
        )

        if capability_name is None:
            return None

        return self.registry.resolve(
            capability_name
        )
