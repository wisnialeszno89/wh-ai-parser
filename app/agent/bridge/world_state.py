from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class WorldElement:
    kind: str
    label: str | None = None
    interaction_capability: str = "unknown"
    current_value: str | None = None
    confidence: float | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "label": self.label,
            "interaction_capability": self.interaction_capability,
        }
        if self.current_value is not None:
            payload["current_value"] = self.current_value
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload


@dataclass(frozen=True)
class WorldState:
    """
    Stable, provider-neutral snapshot of the world exposed to NaviMind.

    Runtime handles, coordinates, automation ids and screenshots are
    deliberately excluded from this contract.
    """

    active_application: str | None = None
    active_window_title: str | None = None
    visible_elements: tuple[WorldElement, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def from_scene(cls, scene) -> "WorldState":
        if scene is None:
            return cls()

        state = scene.observation.state
        elements: list[WorldElement] = []
        for element in scene.elements[:100]:
            metadata = element.metadata or {}
            current_value = metadata.get("current_value")
            elements.append(
                WorldElement(
                    kind=element.kind,
                    label=element.label,
                    interaction_capability=element.interaction_capability.value,
                    current_value=(
                        current_value
                        if isinstance(current_value, str)
                        else None
                    ),
                    confidence=element.confidence,
                )
            )

        return cls(
            active_application=state.active_application,
            active_window_title=state.active_window_title,
            visible_elements=tuple(elements),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "active_application": self.active_application,
            "active_window_title": self.active_window_title,
            "visible_elements": [
                element.to_payload()
                for element in self.visible_elements
            ],
            "element_count": len(self.visible_elements),
        }
