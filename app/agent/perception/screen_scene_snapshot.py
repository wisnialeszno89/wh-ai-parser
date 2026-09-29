from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ScreenElementSnapshot:
    element_id: str | None
    kind: str
    label: str | None
    x: int | None
    y: int | None
    width: int | None
    height: int | None
    confidence: float | None
    interaction_capability: str
    evidence: tuple[Mapping[str, object], ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class ScreenSceneSnapshot:
    elements: tuple[ScreenElementSnapshot, ...]
    metadata: Mapping[str, object]

    @classmethod
    def from_scene(cls, scene):
        elements = tuple(
            ScreenElementSnapshot(
                element_id=(
                    element.metadata.get("tracked_object_id")
                    if element.metadata
                    else None
                ),
                kind=cls._normalize_kind(element.kind),
                label=element.label,
                x=element.x,
                y=element.y,
                width=element.width,
                height=element.height,
                confidence=element.confidence,
                interaction_capability=cls._normalize_kind(
                    element.interaction_capability,
                ),
                evidence=tuple(
                    cls._evidence_to_mapping(item)
                    for item in element.evidence
                ),
                metadata=dict(element.metadata or {}),
            )
            for element in scene.elements
        )

        return cls(
            elements=elements,
            metadata=dict(scene.metadata),
        )

    @staticmethod
    def _evidence_to_mapping(evidence):
        return {
            "source": ScreenSceneSnapshot._normalize_kind(evidence.source),
            "kind": ScreenSceneSnapshot._normalize_kind(evidence.kind),
            "value": evidence.value,
            "confidence": evidence.confidence,
            "element_id": evidence.element_id,
            "observed": evidence.observed,
            "metadata": dict(evidence.metadata),
        }

    @staticmethod
    def _normalize_kind(value):
        if value is None:
            return "unknown"

        raw = getattr(value, "value", value)

        if isinstance(raw, str):
            return raw.strip().casefold()

        return str(raw).strip().casefold()
