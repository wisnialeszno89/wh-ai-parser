from __future__ import annotations

from dataclasses import dataclass, field

from app.agent.perception.screen_scene import ScreenScene


@dataclass(frozen=True)
class SemanticSnapshot:
    """
    Model-safe snapshot of the meaningful state visible to the agent.

    Deliberately excludes coordinates, handles, automation ids, runtime
    identifiers and executor/provider internals so learned workflows remain
    semantic and portable between machines and applications.
    """

    application: str | None = None
    window_title: str | None = None
    active_document: str | None = None
    elements: tuple[dict[str, object], ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_scene(
        cls,
        scene: ScreenScene | None,
        *,
        max_elements: int = 80,
    ) -> "SemanticSnapshot":
        if scene is None:
            return cls()

        state = scene.observation.state
        elements: list[dict[str, object]] = []

        for element in scene.elements[:max_elements]:
            item: dict[str, object] = {
                "kind": element.kind,
                "label": element.label,
                "interaction_capability": (
                    element.interaction_capability.value
                ),
            }

            if element.confidence is not None:
                item["confidence"] = element.confidence

            metadata = element.metadata or {}
            for key in (
                "current_value",
                "semantic_label",
                "semantic_name",
                "role",
                "document_scope",
                "uia_tab_scope",
                "uia_document_tab_selected",
            ):
                value = metadata.get(key)
                if isinstance(value, (str, int, float, bool)):
                    item[key] = value

            elements.append(item)

        return cls(
            application=state.active_application,
            window_title=state.active_window_title,
            active_document=scene.active_document,
            elements=tuple(elements),
            metadata={
                "element_count": len(scene.elements),
                "included_element_count": len(elements),
            },
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "application": self.application,
            "window_title": self.window_title,
            "active_document": self.active_document,
            "elements": list(self.elements),
            "metadata": dict(self.metadata),
        }
