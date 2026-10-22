"""Read-only diagnostic for the local PDF-to-WindowHub workflow.

This command observes the current foreground window through the existing
Windows environment/UIA providers. It does not instantiate the task runner or
executor, call NaviMind, save screenshots, click, type, or submit anything.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from typing import Any


_FIELD_ALIASES = {
    "product_type": {
        "product type", "rodzaj produktu", "typ produktu", "produkt",
        "product",
    },
    "quantity": {
        "quantity", "qty", "ilosc", "liczba", "sztuk", "sztuki",
    },
    "width": {"width", "szerokosc", "szer"},
    "height": {"height", "wysokosc", "wys"},
}
_CONTROL_LABELS = {
    "nowa oferta",
    "dodaj artykul do konstrukcji",
    "ok",
    "anuluj",
    "zakoncz",
    "zapisz szkic",
    "zapisz",
    "save draft",
    "finish",
    "okno",
    "okna",
    "window",
    "windows",
    "drzwi",
    "door",
    "drzwi balkonowe",
    "balcony door",
    "przesuwne",
    "sliding door",
    "hs",
}
_NUMERIC_VALUE = re.compile(
    r"^[+-]?\d+(?:[.,]\d+)?"
    r"(?:\s*(?:mm|cm|m|szt\.?|sztuk|sztuki|pcs?|pieces?))?$",
    re.IGNORECASE,
)


def _canonical(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _field_for_label(label: str) -> str | None:
    normalized = _canonical(label)
    for field_name, aliases in _FIELD_ALIASES.items():
        if normalized in {_canonical(alias) for alias in aliases}:
            return field_name
    return None


def _safe_field_value(field_name: str, value: object) -> tuple[object, bool]:
    if value is None or value == "":
        return None, False
    if field_name in {"width", "height", "quantity"} and isinstance(value, (str, int, float)):
        candidate = str(value).strip()
        if _NUMERIC_VALUE.fullmatch(candidate):
            return candidate, False
    # Do not leak arbitrary text from the active business document.
    return "[redacted: non-numeric or unsupported value]", True


def build_report(scene: object) -> dict[str, object]:
    """Create a compact, privacy-conscious report from one observed scene."""
    observation = getattr(scene, "observation", None)
    state = getattr(observation, "state", None)
    observation_metadata = getattr(observation, "metadata", {}) or {}
    scene_metadata = getattr(scene, "metadata", {}) or {}
    elements = tuple(getattr(scene, "elements", ()) or ())

    window_title = getattr(state, "active_window_title", None)
    active_document = getattr(scene, "active_document", None)
    if not isinstance(active_document, str) or not active_document.strip():
        candidate = scene_metadata.get("active_document")
        active_document = candidate if isinstance(candidate, str) and candidate.strip() else None

    fields: list[dict[str, object]] = []
    controls: list[dict[str, object]] = []
    redacted_value_count = 0
    scope_ready_field_count = 0

    for element in elements:
        label = getattr(element, "label", None)
        kind = getattr(element, "kind", None)
        if not isinstance(label, str) or not label.strip():
            continue
        label = label.strip()
        metadata = getattr(element, "metadata", None) or {}
        if not isinstance(metadata, dict) and not hasattr(metadata, "get"):
            metadata = {}

        field_name = _field_for_label(label)
        if field_name is not None:
            raw_value = metadata.get("current_value")
            safe_value, was_redacted = _safe_field_value(field_name, raw_value)
            redacted_value_count += int(was_redacted)
            scope = metadata.get("document_scope")
            owned_modal = metadata.get("uia_owned_modal") is True
            active_scoped = (
                isinstance(active_document, str)
                and isinstance(scope, str)
                and scope.strip() == active_document.strip()
            )
            scope_proven = active_scoped or owned_modal
            scope_ready_field_count += int(scope_proven)
            fields.append({
                "field": field_name,
                "label": label,
                "control_kind": kind,
                "value": safe_value,
                "value_redacted": was_redacted,
                "enabled": metadata.get("uia_enabled"),
                "selected": metadata.get("uia_selected"),
                "active_document_scope_proven": active_scoped,
                "owned_modal_scope_proven": owned_modal,
                "write_scope_proven": scope_proven,
            })

        normalized_label = _canonical(label)
        if (
            normalized_label in {_canonical(item) for item in _CONTROL_LABELS}
            or normalized_label.startswith("dodaj artykul do konstrukcji")
        ):
            controls.append({
                "label": label,
                "control_kind": kind,
                "enabled": metadata.get("uia_enabled"),
                "selected": metadata.get("uia_selected"),
                "owned_modal": metadata.get("uia_owned_modal") is True,
            })

    fields.sort(key=lambda item: (str(item["field"]), str(item["label"]).casefold()))
    controls.sort(key=lambda item: str(item["label"]).casefold())

    title_text = window_title if isinstance(window_title, str) else ""
    windowhub_title_match = "windowhub" in _canonical(title_text)
    focus_value = observation_metadata.get("window_focused")

    all_expected_fields_seen = all(
        any(item["field"] == field_name for item in fields)
        for field_name in ("product_type", "quantity", "width", "height")
    )
    all_seen_fields_scoped = bool(fields) and all(
        item["write_scope_proven"] is True for item in fields
    )

    if not windowhub_title_match:
        next_step = "Activate the WindowHub main window and run this read-only probe again."
    elif not all_expected_fields_seen:
        next_step = "Review the reported labels; missing fields may be hidden, on another screen, or not exposed by UI Automation."
    elif not all_seen_fields_scoped:
        next_step = "Do not run live text entry yet; target document/modal scope is not proven for every observed field."
    else:
        next_step = "Observation contract looks promising; review the labels and scope, then perform a separately approved low-risk draft test."

    return {
        "probe": "windowhub_pdf_quote_read_only",
        "read_only": True,
        "desktop_actions_executed": 0,
        "network_calls": 0,
        "screenshot_saved": False,
        "active_application": getattr(state, "active_application", None),
        "windowhub_title_match": windowhub_title_match,
        "active_window_title_length": len(title_text),
        "active_window_focused": focus_value,
        "active_document_resolved": bool(active_document),
        "active_document_resolution": scene_metadata.get(
            "active_document_resolution", "not_reported"
        ),
        "document_tab_count": scene_metadata.get("document_tab_count", 0),
        "selected_document_tab_count": scene_metadata.get(
            "selected_document_tab_count", 0
        ),
        "observed_semantic_element_count": len(elements),
        "quote_field_candidates": fields,
        "workflow_control_candidates": controls,
        "redacted_value_count": redacted_value_count,
        "all_basic_quote_fields_seen": all_expected_fields_seen,
        "all_observed_fields_have_write_scope": all_seen_fields_scoped,
        "recommended_next_step": next_step,
    }


def main() -> int:
    """Observe the current WindowHub scene without building an executor."""
    if os.name != "nt":
        print("ERROR: this diagnostic requires Windows UI Automation.")
        return 2

    try:
        # These are perception-only components. Deliberately do not import or
        # instantiate AgentRuntime, RobotGUIExecutor, or a task runner here.
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        from app.agent.perception.perception_engine import PerceptionEngine
        from app.agent.perception.windows_ui_automation_provider import (
            WindowsUIAutomationProvider,
        )

        environment = WindowsDesktopEnvironmentAdapter()
        perception = PerceptionEngine(
            providers=(WindowsUIAutomationProvider(),),
        )
        observation = environment.observe()
        scene = perception.perceive(observation)
        report = build_report(scene)
    except Exception as exc:
        # Do not print traceback details, window handles, or filesystem paths.
        print(json.dumps({
            "probe": "windowhub_pdf_quote_read_only",
            "read_only": True,
            "error": type(exc).__name__,
            "message": "Observation failed. No click/type/task action was attempted.",
            "desktop_actions_executed": 0,
            "network_calls": 0,
        }, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["windowhub_title_match"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
