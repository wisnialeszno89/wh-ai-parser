from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)


class FakeEnvironment(EnvironmentAdapter):
    """
    Deterministic environment implementation for tests.

    This allows the agent environment layer to be developed
    and tested without requiring Windows, WH, GUI access
    or computer vision.
    """

    def __init__(
        self,
        state: EnvironmentState,
        metadata: dict[str, object] | None = None,
    ) -> None:

        self.state = state

        self.metadata = (
            metadata
            if metadata is not None
            else {}
        )

        self.observe_count = 0

    def observe(
        self,
    ) -> EnvironmentObservation:

        self.observe_count += 1

        return EnvironmentObservation(
            state=self.state,
            metadata=dict(self.metadata),
        )
