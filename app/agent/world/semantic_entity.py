from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemanticEntity:
    """
    Model-facing representation of something meaningful in the current UI.

    This is intentionally independent from a particular GUI technology.
    Physical targeting data remains in the local ScreenElement/runtime layer.
    """

    kind: str
    label: str | None = None
    current_value: str | None = None
    role: str | None = None
    document_scope: str | None = None
    confidence: float | None = None
    affordance_names: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def semantic_name(self) -> str | None:
        for value in (
            self.label,
            self.metadata.get("semantic_label"),
            self.metadata.get("semantic_name"),
            self.metadata.get("name"),
        ):
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "label": self.label,
            "current_value": self.current_value,
            "role": self.role,
            "document_scope": self.document_scope,
            "confidence": self.confidence,
            "affordances": list(self.affordance_names),
        }

        for key, value in self.metadata.items():
            if key in {
                "semantic_label",
                "semantic_name",
                "name",
                "description",
                "scope_status",
            } and isinstance(value, (str, bool, int, float)):
                payload[key] = value

        return payload
