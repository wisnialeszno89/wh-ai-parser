"""Build a provider-neutral v2 world snapshot from the existing ScreenScene.

This is a projection of current perception data, not a second world model.
Native identity and geometry remain in a local-only reference map.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


MAX_WORLD_ENTITIES = 200
MAX_WORLD_EVIDENCE = 100
MAX_WORLD_AFFORDANCES = 200
MAX_EVIDENCE_PER_ELEMENT = 12
MAX_EVIDENCE_VALUE_DEPTH = 4
MAX_EVIDENCE_COLLECTION_ITEMS = 32

# Geometry and native/provider identity are intentionally never projected.
_PRIVATE_KEYS = frozenset(
    {
        "x",
        "y",
        "left",
        "top",
        "right",
        "bottom",
        "width",
        "height",
        "bounds",
        "position",
        "coordinates",
        "screen_coordinates",
        "window_handle",
        "hwnd",
        "runtime_id",
        "uia_runtime_id",
        "automation_id",
        "provider_id",
        "provider_element_id",
        "native_id",
        "tracked_object_id",
        "element_id",
        "executor",
        "screenshot",
    }
)
_PRIVATE_EVIDENCE_KINDS = frozenset({"bounds", "position"})
_CONFIRMATION_LABEL_TERMS = (
    "delete",
    "remove",
    "submit",
    "send",
    "pay",
    "purchase",
    "buy",
    "approve",
    "place order",
    "löschen",
    "entfernen",
    "senden",
    "bezahlen",
    "kaufen",
    "bestellen",
    "freigeben",
    "stornieren",
)
_UNSUPPORTED = object()


def _enum_text(value: object) -> str | None:
    raw = value.value if isinstance(value, Enum) else value
    if not isinstance(raw, str):
        return None
    normalized = raw.strip()
    return normalized or None


def _safe_json_value(value: object, depth: int = 0) -> object:
    """Copy only bounded JSON primitives, excluding provider/native fields."""
    if depth > MAX_EVIDENCE_VALUE_DEPTH:
        return _UNSUPPORTED
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str) and len(value) > 2_000:
            return value[:2_000]
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else _UNSUPPORTED
    if isinstance(value, Enum):
        return _safe_json_value(value.value, depth + 1)
    if isinstance(value, (tuple, list)):
        if len(value) > MAX_EVIDENCE_COLLECTION_ITEMS:
            return _UNSUPPORTED
        result = []
        for item in value:
            safe = _safe_json_value(item, depth + 1)
            if safe is _UNSUPPORTED:
                return _UNSUPPORTED
            result.append(safe)
        return result
    if isinstance(value, Mapping):
        if len(value) > MAX_EVIDENCE_COLLECTION_ITEMS:
            return _UNSUPPORTED
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                return _UNSUPPORTED
            normalized_key = key.strip().casefold().replace("-", "_")
            if normalized_key in _PRIVATE_KEYS:
                continue
            safe = _safe_json_value(item, depth + 1)
            if safe is _UNSUPPORTED:
                return _UNSUPPORTED
            result[key[:128]] = safe
        return result
    return _UNSUPPORTED


def _requires_confirmation(label: str) -> bool:
    normalized = " ".join(label.casefold().split())
    return any(
        term in normalized
        for term in _CONFIRMATION_LABEL_TERMS
    )


def _build_affordances(
    elements: tuple[ScreenElement, ...],
) -> list[dict[str, object]]:
    """Describe bounded, evidence-backed UI actions without exposing native ids."""
    affordances: list[dict[str, object]] = []

    for index, element in enumerate(elements, start=1):
        label = element.label.strip() if isinstance(element.label, str) else ""
        metadata = element.metadata or {}
        capability = _enum_text(element.interaction_capability)

        if capability != "clickable" or not label:
            continue
        if metadata.get("uia_enabled") is False:
            continue
        if metadata.get("uia_visible") is False:
            continue

        control_type = (
            metadata.get("uia_control_type")
            or metadata.get("control_type")
            or element.kind
        )
        control_type = (
            control_type.strip().casefold()
            if isinstance(control_type, str)
            else ""
        )

        actions = [
            (
                "click",
                f"Click the visible control labeled '{label}'.",
                _requires_confirmation(label),
            )
        ]
        if control_type in {"edit", "combobox"}:
            actions.append(
                (
                    "write_text",
                    f"Enter text in the editable control labeled '{label}'.",
                    False,
                )
            )

        for action_name, description, requires_confirmation in actions:
            if len(affordances) >= MAX_WORLD_AFFORDANCES:
                return affordances
            affordances.append(
                {
                    "id": f"aff_{len(affordances) + 1:04d}",
                    "entity_ref": f"ent_{index:04d}",
                    "name": action_name,
                    "description": description,
                    "requires_confirmation": requires_confirmation,
                }
            )

    return affordances


def _timestamp(value: str | None) -> str:
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("observed_at must be a non-empty ISO timestamp.")
        return value.strip()
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class SemanticReferenceMap:
    """Private, task- and revision-scoped mapping from opaque refs to local elements."""

    task_id: str
    world_revision: int
    _elements: Mapping[str, ScreenElement] = field(repr=False, compare=False)

    def resolve(
        self,
        ref: str,
        *,
        task_id: str,
        world_revision: int,
    ) -> ScreenElement:
        if task_id != self.task_id:
            raise ValueError("semantic_reference_task_mismatch")
        if world_revision != self.world_revision:
            raise ValueError("semantic_reference_revision_mismatch")
        try:
            return self._elements[ref]
        except KeyError as exc:
            raise KeyError("semantic_reference_unknown") from exc

    def ref_for(
        self,
        element: ScreenElement,
        *,
        task_id: str,
        world_revision: int,
    ) -> str:
        """Return the unique opaque ref for one exact local ScreenElement."""
        if task_id != self.task_id:
            raise ValueError("semantic_reference_task_mismatch")
        if world_revision != self.world_revision:
            raise ValueError("semantic_reference_revision_mismatch")

        matches = [
            ref
            for ref, candidate in self._elements.items()
            if candidate is element
        ]
        if len(matches) != 1:
            raise ValueError("semantic_reference_element_not_unique")
        return matches[0]

    @property
    def refs(self) -> tuple[str, ...]:
        return tuple(self._elements.keys())


@dataclass(frozen=True)
class AgentTaskV2WorldSnapshot:
    """Model-safe world payload plus a local-only reference resolver."""

    payload: Mapping[str, object]
    reference_map: SemanticReferenceMap


class AgentTaskV2WorldBuilder:
    """Project the existing ScreenScene and its evidence into the v2 world shape."""

    def build(
        self,
        scene: ScreenScene | None,
        *,
        task_id: str,
        world_revision: int,
        observed_at: str | None = None,
    ) -> AgentTaskV2WorldSnapshot:
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string.")
        if isinstance(world_revision, bool) or not isinstance(world_revision, int):
            raise ValueError("world_revision must be an integer.")
        if world_revision < 0:
            raise ValueError("world_revision must not be negative.")

        timestamp = _timestamp(observed_at)
        state = scene.observation.state if scene is not None else None
        application = (
            state.active_application
            if state is not None
            else None
        )
        window_title = (
            state.active_window_title
            if state is not None
            else None
        )

        elements = tuple(scene.elements) if scene is not None else ()
        selected_elements = elements[:MAX_WORLD_ENTITIES]
        local_map: dict[str, ScreenElement] = {}
        entities: list[dict[str, object]] = []
        evidence: list[dict[str, object]] = []
        omitted_evidence = 0

        for index, element in enumerate(selected_elements, start=1):
            entity_ref = f"ent_{index:04d}"
            local_map[entity_ref] = element

            capability = _enum_text(element.interaction_capability) or "unknown"
            current_value = (element.metadata or {}).get("current_value")
            value_present = (
                isinstance(current_value, str)
                and bool(current_value.strip())
            )

            state_payload: dict[str, object] = {
                "interaction_capability": capability,
            }
            if isinstance(current_value, str):
                state_payload["value_present"] = value_present

            evidence_refs: list[str] = []
            element_evidence = element.evidence[:MAX_EVIDENCE_PER_ELEMENT]
            omitted_evidence += max(
                0,
                len(element.evidence) - len(element_evidence),
            )
            for item in element_evidence:
                kind = _enum_text(item.kind)
                source = _enum_text(item.source)
                if (
                    kind is None
                    or source is None
                    or kind.casefold() in _PRIVATE_EVIDENCE_KINDS
                ):
                    continue
                if len(evidence) >= MAX_WORLD_EVIDENCE - 1:
                    omitted_evidence += 1
                    continue

                safe_value = _safe_json_value(item.value)
                if safe_value is _UNSUPPORTED:
                    omitted_evidence += 1
                    continue

                evidence_ref = f"ev_{len(evidence) + 1:04d}"
                evidence_refs.append(evidence_ref)
                evidence.append(
                    {
                        "ref": evidence_ref,
                        "source": source,
                        "observed_at": timestamp,
                        "world_revision": world_revision,
                        "scope": f"{element.kind}:{element.label or 'unlabeled'}"[:512],
                        "confidence": float(item.confidence),
                        "content": {
                            "kind": kind,
                            "value": safe_value,
                            "observed": bool(item.observed),
                        },
                        "limitations": [],
                    }
                )

            confidence = element.confidence
            if confidence is None or not math.isfinite(float(confidence)):
                confidence = 0.0

            entities.append(
                {
                    "ref": entity_ref,
                    "type": str(element.kind)[:128] or "unknown",
                    "label": element.label,
                    "state": state_payload,
                    "attributes": [],
                    "confidence": max(0.0, min(1.0, float(confidence))),
                    "evidence_refs": evidence_refs,
                }
            )

        omitted_entities = max(0, len(elements) - len(selected_elements))
        if omitted_entities or omitted_evidence:
            limitation_messages = []
            if omitted_entities:
                limitation_messages.append(
                    f"{omitted_entities} scene elements omitted by the v2 entity limit."
                )
            if omitted_evidence:
                limitation_messages.append(
                    f"{omitted_evidence} evidence items omitted by v2 projection bounds."
                )
            evidence.append(
                {
                    "ref": f"ev_{len(evidence) + 1:04d}",
                    "source": "runtime",
                    "observed_at": timestamp,
                    "world_revision": world_revision,
                    "scope": "world_projection",
                    "confidence": None,
                    "content": {
                        "kind": "projection_limitations",
                        "omitted_entities": omitted_entities,
                        "omitted_evidence": omitted_evidence,
                    },
                    "limitations": limitation_messages,
                }
            )

        world: dict[str, object] = {
            "revision": world_revision,
            "observed_at": timestamp,
            "application": application,
            "window_title": window_title,
            "entities": entities,
            # The current ScreenScene model has no verified relationship graph.
            "relationships": [],
            # Affordances describe observed possibilities; they do not grant
            # execution authority. The local action broker must separately bind
            # and validate every action before it can be dispatched.
            "affordances": _build_affordances(selected_elements),
            "evidence": evidence,
        }


        return AgentTaskV2WorldSnapshot(
            payload=world,
            reference_map=SemanticReferenceMap(
                task_id=task_id,
                world_revision=world_revision,
                _elements=local_map,
            ),
        )
