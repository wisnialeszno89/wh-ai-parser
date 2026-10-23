from dataclasses import dataclass, field
from typing import Mapping

from app.agent.adapters.browser_adapter import BrowserPage
from app.agent.perception.windowhub_grid_reader import WindowHubGridReader


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

    Runtime handles, coordinates, automation ids and provider-local browser
    locators are deliberately excluded from this contract.
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
                    interaction_capability=(
                        element.interaction_capability.value
                    ),
                    current_value=(
                        current_value
                        if isinstance(current_value, str)
                        else None
                    ),
                    confidence=element.confidence,
                )
            )

        # Structured table evidence is not exposed as a GUI affordance.
        # Keep its model-safe payload in world metadata so the NaviMind bridge
        # receives the same OCR table evidence as other task reasoners.
        world_metadata: dict[str, object] = {}
        scene_metadata = getattr(scene, "metadata", {}) or {}
        reconstruction = scene_metadata.get(
            "windowhub_ocr_table_reconstruction"
        )
        if reconstruction is None:
            observation_metadata = (
                getattr(scene.observation, "metadata", {}) or {}
            )
            reconstruction = observation_metadata.get(
                "windowhub_ocr_table_reconstruction"
            )
        serializer = getattr(reconstruction, "to_payload", None)
        if callable(serializer):
            try:
                table_payload = serializer()
            except Exception:
                table_payload = None
            if isinstance(table_payload, dict):
                world_metadata["windowhub_ocr_table"] = table_payload

        # Structured UIA grids are sent separately from visible controls so
        # table data is available even when it falls beyond the 100-element
        # affordance list. Only proven active-document grids are included.
        try:
            active_grids = WindowHubGridReader().read_active_document(scene)
            grid_payloads = [
                grid.to_payload()
                for grid in active_grids[:20]
            ]
        except Exception:
            grid_payloads = []

        if grid_payloads:
            world_metadata["windowhub_grids"] = grid_payloads
            if len(active_grids) > len(grid_payloads):
                world_metadata["windowhub_grids_truncated"] = True

        return cls(
            active_application=state.active_application,
            active_window_title=state.active_window_title,
            visible_elements=tuple(elements),
            metadata=world_metadata,
        )

    @classmethod
    def from_browser_page(
        cls,
        page: BrowserPage | None,
    ) -> "WorldState":
        if page is None:
            return cls()

        elements = tuple(
            WorldElement(
                kind=element.kind,
                label=element.label,
                interaction_capability=(
                    element.interaction_capability
                ).casefold(),
                current_value=element.current_value,
                confidence=element.confidence,
            )
            for element in page.elements[:100]
        )

        return cls(
            active_application="Browser",
            active_window_title=page.title,
            visible_elements=elements,
            metadata={
                "browser_url": page.url,
                "browser_title": page.title,
                "browser_text": page.text,
            },
        )

    def find_elements(
        self,
        label: str,
    ) -> tuple[WorldElement, ...]:
        normalized = label.strip().casefold()

        if not normalized:
            return ()

        return tuple(
            element
            for element in self.visible_elements
            if (
                isinstance(element.label, str)
                and element.label.strip().casefold()
                == normalized
            )
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
            "metadata": dict(self.metadata),
        }
