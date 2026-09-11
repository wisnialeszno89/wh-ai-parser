from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)


class EnvironmentRuntime:
    """
    Runtime facade for observing the external environment.

    The runtime hides the concrete adapter implementation
    from the rest of the agent.
    """

    def __init__(
        self,
        adapter: EnvironmentAdapter,
    ) -> None:
        self.adapter = adapter

    def observe(
        self,
    ) -> EnvironmentObservation:
        return self.adapter.observe()
