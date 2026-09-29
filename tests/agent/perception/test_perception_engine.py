from dataclasses import dataclass

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.perception.perception_provider import (
    PerceptionProvider,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)


@dataclass
class StaticProvider(PerceptionProvider):
    elements: tuple[ScreenElement, ...]

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        return self.elements


def test_perception_engine_aggregates_provider_results() -> None:
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="test",
        )
    )

    providers = (
        StaticProvider(
            elements=(
                ScreenElement(
                    kind="button",
                    label="A",
                ),
            )
        ),
        StaticProvider(
            elements=(
                ScreenElement(
                    kind="icon",
                    label="B",
                ),
            )
        ),
    )

    scene = PerceptionEngine(
        providers=providers,
    ).perceive(observation)

    assert len(scene.elements) == 2
    assert scene.elements[0].label == "A"
    assert scene.elements[1].label == "B"
    assert scene.metadata["provider_count"] == 2
