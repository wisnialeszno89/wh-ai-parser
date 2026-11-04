"""Privacy-conscious teach-by-demonstration for WindowHub.

Observe the salesperson's *manual* workflow and learn stage transitions and
control-state changes, not pixel coordinates, typed text or mouse positions.
This is a passive recorder, not an input hook and not model training.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from app.agent.perception.screen_scene import ScreenScene


KNOWN_STAGES = {
    "okna - start1": "start",
    "właściwości dokumentu": "document_properties",
    "zakładanie nowego klienta": "new_customer",
    "dodawanie nowej pozycji": "position",
    "wielkość okna": "dimensions",
    "podstawowe parametry okna": "basic_parameters",
    "parametry szklenia": "glazing",
    "parametry okuć": "hardware",
    "modyfikator": "modifier",
}
MODEL_SAFE_LABELS = frozenset({
    "NOWA OFERTA", "OK", "Anuluj", "Dalej >", "< Wstecz", "Firma",
    "Szerokość", "Wysokość", "Ile sztuk", "Wybierz kolor profili",
    "Dodaj nowego klienta", "Wybierz istniejącego klienta",
    "Bez ceny konstrukcji", "Bez ceny montażu", "Bez ceny demontażu",
    "Bez ceny wykończenia", "Zakończ",
})


def stage_of(scene: ScreenScene) -> str | None:
    state = scene.observation.state
    process = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if process != "okna.exe":
        return None
    title = (state.active_window_title or "").strip().casefold()
    if title.startswith("okna - ofr/"):
        return "offer_document"
    return KNOWN_STAGES.get(title, "windowhub_unmapped")


def _safe_control_label(element) -> str | None:
    metadata = element.metadata or {}
    label = metadata.get("semantic_label") or element.label
    if label in MODEL_SAFE_LABELS:
        return label
    return None


def semantic_snapshot(scene: ScreenScene) -> dict[str, Any] | None:
    """Snapshot of stable UIA control structure; never record customer values."""
    stage = stage_of(scene)
    if stage is None:
        return None
    candidates: dict[str, dict[str, object]] = {}
    duplicates: set[str] = set()
    for element in scene.elements:
        meta = element.metadata or {}
        identifier = meta.get("automation_id")
        if (
            meta.get("source") not in {"windows_ui_automation", "windowhub_ui_automation"}
            or meta.get("uia_visible") is not True
            or not isinstance(identifier, str)
            or not identifier.strip()
            or not (identifier.startswith("IDC_") or identifier.isdecimal())
            or identifier.casefold().startswith("part_")
        ):
            continue
        if element.kind not in {"button", "edit", "checkbox", "combobox", "radiobutton", "tabitem"}:
            continue
        key = f"{element.kind}:{identifier[:100]}"
        if key in candidates:
            duplicates.add(key)
            continue
        state = {}
        for source, name in (
            ("uia_checked", "checked"),
            ("uia_selected", "selected"),
            ("uia_enabled", "enabled"),
            ("uia_focused", "focused"),
        ):
            value = meta.get(source)
            if isinstance(value, bool):
                state[name] = value
        value = meta.get("current_value")
        if isinstance(value, str):
            state["value_present"] = bool(value.strip())
        candidates[key] = {
            "role": element.kind,
            "label": _safe_control_label(element),
            "state": state,
        }
    for key in duplicates:
        candidates.pop(key, None)
    # Private native IDs remain local and are not included in model-facing experiences.
    return {"stage": stage, "controls": dict(list(sorted(candidates.items()))[:150])}


def semantic_transition(before: Mapping[str, object], after: Mapping[str, object]) -> dict[str, object] | None:
    """Infer effects only; the recorder does not claim which control was clicked."""
    old = before.get("controls") or {}
    new = after.get("controls") or {}
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise ValueError("invalid_demo_snapshot")
    changed = []
    for key in sorted(old.keys() & new.keys()):
        a = old[key]
        b = new[key]
        if a.get("state") != b.get("state"):
            changed.append({
                "role": b.get("role"),
                "label": b.get("label"),
                "before": a.get("state"),
                "after": b.get("state"),
            })
    result = {
        "from_stage": before.get("stage"),
        "to_stage": after.get("stage"),
        "changed": changed[:20],
        "control_count_before": len(old),
        "control_count_after": len(new),
    }
    if result["from_stage"] == result["to_stage"] and not changed:
        return None
    return result


def demonstration_experience(records: list[Mapping[str, object]], *, limit: int = 12) -> tuple[dict[str, object], ...]:
    """Promote only stage transitions to model context, not unverified actions."""
    if not 1 <= limit <= 20:
        raise ValueError("invalid_experience_limit")
    items = []
    seen = set()
    for record in records:
        if record.get("type") != "transition":
            continue
        change = record.get("transition")
        if not isinstance(change, dict):
            continue
        old, new = change.get("from_stage"), change.get("to_stage")
        safe_stages = set(KNOWN_STAGES.values()) | {"offer_document"}
        if (
            not isinstance(old, str) or not isinstance(new, str)
            or old == new or old not in safe_stages or new not in safe_stages
        ):
            continue
        if (old, new) in seen:
            continue
        seen.add((old, new))
        items.append({
            "source": "human_demonstration",
            "observed_from_stage": old[:80],
            "observed_to_stage": new[:80],
            "certainty": "observed_transition_not_causal_action",
        })
        if len(items) >= limit:
            break
    return tuple(items)
