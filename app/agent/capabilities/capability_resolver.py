from app.agent.capabilities.capability import Capability
from app.agent.capabilities.capability_registry import (
    CapabilityRegistry,
)


class CapabilityResolver:
    """
    Resolves named capabilities from the available registry.

    Intent-to-capability routing will be added separately.
    Keeping this class simple prevents business logic from
    leaking into the registry itself.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
    ) -> None:
        self.registry = registry

    def resolve(
        self,
        name: str,
    ) -> Capability | None:
        return self.registry.resolve(name)
