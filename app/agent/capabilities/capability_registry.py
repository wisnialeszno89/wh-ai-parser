from app.agent.capabilities.capability import Capability


class CapabilityRegistry:
    """
    Registry of capabilities available to the agent.

    This layer is intentionally independent from planning
    and execution. The planner can later ask the registry
    what areas of competence are available.
    """

    def __init__(
        self,
        capabilities: tuple[Capability, ...] = (),
    ) -> None:
        self._capabilities = {
            capability.name: capability
            for capability in capabilities
        }

    def register(
        self,
        capability: Capability,
    ) -> None:
        self._capabilities[
            capability.name
        ] = capability

    def resolve(
        self,
        name: str,
    ) -> Capability | None:
        return self._capabilities.get(name)

    def all(
        self,
    ) -> tuple[Capability, ...]:
        return tuple(
            self._capabilities.values()
        )

    def supports(
        self,
        name: str,
    ) -> bool:
        return name in self._capabilities
