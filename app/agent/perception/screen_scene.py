from dataclasses import dataclass, field

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)


@dataclass(frozen=True)
class ScreenScene:
    """
    Semantic scene representing what the agent currently
    understands about the visible environment.

    EnvironmentObservation describes the raw environment.

    ScreenScene describes the interpreted visible scene.
    """

    observation: EnvironmentObservation

    elements: tuple[ScreenElement, ...] = ()

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    def elements_of_kind(
        self,
        kind: str,
    ) -> tuple[ScreenElement, ...]:

        return tuple(
            element
            for element in self.elements
            if element.kind == kind
        )

    def find_by_label(
        self,
        label: str,
    ) -> tuple[ScreenElement, ...]:

        normalized = label.casefold()

        return tuple(
            element
            for element in self.elements
            if (
                element.label is not None
                and element.label.casefold()
                == normalized
            )
        )
