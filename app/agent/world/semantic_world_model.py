from __future__ import annotations

from dataclasses import dataclass, field

from app.agent.perception.screen_scene import ScreenScene
from app.agent.world.affordance import Affordance
from app.agent.world.semantic_entity import SemanticEntity


@dataclass(frozen=True)
class SemanticWorldModel:
    """
    Current semantic world understood by the digital worker.

    It is a snapshot, not a database. The runtime can rebuild it after every
    observation so the reasoner always works from the latest visible state.
    """

    application: str | None = None
    window_title: str | None = None
    active_document: str | None = None
    entities: tuple[SemanticEntity, ...] = ()
    affordances: tuple[Affordance, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_scene(
        cls,
        scene: ScreenScene | None,
        *,
        max_entities: int = 100,
    ) -> "SemanticWorldModel":
        if scene is None:
            return cls()

        state = scene.observation.state
        entities: list[SemanticEntity] = []
        affordances: list[Affordance] = []

        for element in scene.elements[:max_entities]:
            metadata = dict(element.metadata or {})
            current_value = metadata.get("current_value")
            current_value = (
                current_value
                if isinstance(current_value, str)
                else None
            )

            role = metadata.get("role")
            role = role if isinstance(role, str) else None

            document_scope = metadata.get("document_scope")
            document_scope = (
                document_scope
                if isinstance(document_scope, str)
                else None
            )

            affordance_names: list[str] = []

            if element.interaction_capability.value == "clickable":
                affordance_names.append("click_screen_element")

            if current_value is not None or element.kind.casefold() in {
                "edit",
                "textbox",
                "input",
                "combobox",
            }:
                affordance_names.append("write_text")

            entity = SemanticEntity(
                kind=element.kind,
                label=element.label,
                current_value=current_value,
                role=role,
                document_scope=document_scope,
                confidence=element.confidence,
                affordance_names=tuple(dict.fromkeys(affordance_names)),
                metadata={
                    key: value
                    for key, value in metadata.items()
                    if key in {
                        "semantic_label",
                        "semantic_name",
                        "name",
                        "description",
                        "scope_status",
                    }
                },
            )
            entities.append(entity)

            target = entity.semantic_name()
            if target is not None:
                if "click_screen_element" in affordance_names:
                    affordances.append(
                        Affordance(
                            action_name="click_screen_element",
                            target=target,
                            description=f"Select or activate '{target}'.",
                            confidence=(
                                element.confidence
                                if element.confidence is not None
                                else 0.0
                            ),
                        )
                    )

                if "write_text" in affordance_names:
                    affordances.append(
                        Affordance(
                            action_name="write_text",
                            target=target,
                            description=f"Enter text into '{target}'.",
                            confidence=(
                                element.confidence
                                if element.confidence is not None
                                else 0.0
                            ),
                        )
                    )

        return cls(
            application=state.active_application,
            window_title=state.active_window_title,
            active_document=scene.active_document,
            entities=tuple(entities),
            affordances=tuple(affordances),
            metadata={
                "entity_count": len(scene.elements),
                "included_entity_count": len(entities),
            },
        )

    def find_entities(
        self,
        label: str,
    ) -> tuple[SemanticEntity, ...]:
        normalized = label.strip().casefold()

        return tuple(
            entity
            for entity in self.entities
            if (
                isinstance(entity.semantic_name(), str)
                and entity.semantic_name().casefold() == normalized
            )
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "application": self.application,
            "window_title": self.window_title,
            "active_document": self.active_document,
            "entities": [
                entity.to_payload()
                for entity in self.entities
            ],
            "affordances": [
                affordance.to_payload()
                for affordance in self.affordances
            ],
            "metadata": dict(self.metadata),
        }
