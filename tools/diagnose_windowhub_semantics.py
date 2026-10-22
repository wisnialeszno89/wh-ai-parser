"""Read-only semantic inventory for a locally open WindowHub window.

This diagnostic deliberately avoids task reasoning, the execution engine, mouse/
keyboard APIs, screenshot persistence, checkpoint creation, and network calls.
It observes the active top-level WindowHub window through the existing
Windows UI Automation perception provider and prints a redacted JSON report.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path

sys.dont_write_bytecode = True

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _optional_bool(metadata: Mapping[str, object], *keys: str) -> bool | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, bool):
            return value
    return None


def _document_scope_status(
    metadata: Mapping[str, object],
    active_document: str | None,
) -> str:
    raw_scope = metadata.get("document_scope")
    if not isinstance(raw_scope, str) or not raw_scope.strip():
        return "unknown"
    if not isinstance(active_document, str) or not active_document.strip():
        return "scope_present_active_document_unresolved"
    return (
        "active_document"
        if raw_scope.strip() == active_document.strip()
        else "other_document"
    )


def build_read_only_report(
    scene: object | None,
    *,
    active_window_title: str | None,
    window_focused: bool | None,
    include_sensitive_values: bool = False,
    max_elements: int = 100,
    stop_reason: str | None = None,
) -> dict[str, object]:
    """Build a JSON-safe report without exposing UIA runtime identifiers/handles."""
    if not isinstance(max_elements, int) or isinstance(max_elements, bool) or not 1 <= max_elements <= 500:
        raise ValueError("max_elements must be an integer between 1 and 500.")

    title = active_window_title.strip() if isinstance(active_window_title, str) else ""
    title_matches = "windowhub" in title.casefold()
    metadata = getattr(scene, "metadata", None) or {}
    if not isinstance(metadata, Mapping):
        metadata = {}
    elements = tuple(getattr(scene, "elements", ()) or ())
    active_document = getattr(scene, "active_document", None)
    if not isinstance(active_document, str) or not active_document.strip():
        active_document = None

    inventory: list[dict[str, object]] = []
    scoped_count = 0
    for index, element in enumerate(elements[:max_elements], start=1):
        element_metadata = getattr(element, "metadata", None) or {}
        if not isinstance(element_metadata, Mapping):
            element_metadata = {}
        label = getattr(element, "label", None)
        label = label.strip() if isinstance(label, str) else ""
        capability = getattr(element, "interaction_capability", None)
        capability = getattr(capability, "value", capability)
        current_value = element_metadata.get("current_value")
        value_available = isinstance(current_value, str)
        scope_raw = element_metadata.get("document_scope")
        if isinstance(scope_raw, str) and scope_raw.strip():
            scoped_count += 1

        tab_scope = element_metadata.get("uia_tab_scope")
        tab_scope = (
            tab_scope
            if isinstance(tab_scope, str)
            and tab_scope in {"document", "application", "unknown"}
            else None
        )
        item: dict[str, object] = {
            "index": index,
            "label": label or "<no semantic label>",
            "kind": str(getattr(element, "kind", "") or "unknown"),
            "interaction_capability": str(capability or "unknown"),
            "enabled": _optional_bool(element_metadata, "uia_enabled", "enabled", "is_enabled"),
            "visible": _optional_bool(element_metadata, "uia_visible", "visible"),
            "selected": _optional_bool(element_metadata, "uia_selected", "selected", "checked"),
            "owned_modal": _optional_bool(element_metadata, "uia_owned_modal"),
            "current_value_available": value_available,
            "current_value_nonempty": bool(current_value.strip()) if value_available else None,
            "document_scope_status": _document_scope_status(element_metadata, active_document),
            "raw_document_scope_available": isinstance(scope_raw, str) and bool(scope_raw.strip()),
            "tab_scope": tab_scope,
            "document_tab_selected": _optional_bool(element_metadata, "uia_document_tab_selected"),
        }
        if include_sensitive_values:
            item["current_value"] = current_value if value_available else None
            item["document_scope"] = scope_raw if isinstance(scope_raw, str) else None
        inventory.append(item)

    document_tab_count = metadata.get("document_tab_count")
    selected_document_count = metadata.get("selected_document_tab_count")
    document_resolution = metadata.get("active_document_resolution")
    report: dict[str, object] = {
        "diagnostic": "windowhub_read_only_semantic_inventory",
        "mode": "READ_ONLY",
        "computer_actions_executed": False,
        "network_calls_made": False,
        "files_written": False,
        "screenshot_saved": False,
        "active_window": {
            "title_contains_windowhub": title_matches,
            "title_available": bool(title),
            "focused": window_focused,
            "title": title if include_sensitive_values and title else "<redacted>",
        },
        "active_document": {
            "resolved": active_document is not None,
            "name": active_document if include_sensitive_values else ("<redacted>" if active_document else None),
            "resolution": str(document_resolution or ("resolved" if active_document else "not_observed")),
            "document_tab_count": document_tab_count if isinstance(document_tab_count, int) else None,
            "selected_document_tab_count": selected_document_count if isinstance(selected_document_count, int) else None,
        },
        "inventory": {
            "element_count": len(elements),
            "elements_reported": len(inventory),
            "truncated": len(elements) > max_elements,
            "elements_with_document_scope": scoped_count,
            "elements_without_document_scope": len(elements) - scoped_count,
            "elements_with_current_value": sum(
                1 for item in inventory if item["current_value_available"] is True
            ),
        },
        "elements": inventory,
        "sharing_warning": (
            "Element labels can contain customer or business data. Inspect this report before sharing it. "
            "Current values, active document name, window title, and raw document scopes are redacted by default."
        ),
    }
    if stop_reason:
        report["observation_skipped_reason"] = stop_reason
    return report


def observe_windowhub_scene() -> tuple[object | None, str | None, bool | None, str | None]:
    """Observe active WindowHub via UIA; never constructs a plan or executor."""
    if os.name != "nt":
        raise RuntimeError("This diagnostic must be run on Windows.")

    import ctypes
    import pygetwindow as gw

    window = gw.getActiveWindow()
    if window is None:
        raise RuntimeError("No active top-level window was found.")

    title = (getattr(window, "title", None) or "").strip()
    if "windowhub" not in title.casefold():
        return (
            None,
            title or None,
            None,
            "The active window title does not contain 'WindowHub'; UI Automation inventory was skipped.",
        )

    left = int(window.left)
    top = int(window.top)
    width = int(window.width)
    height = int(window.height)
    if width <= 0 or height <= 0:
        raise RuntimeError("The active WindowHub window has invalid bounds.")

    try:
        window_handle = int(getattr(window, "_hWnd", 0) or 0)
    except (TypeError, ValueError):
        window_handle = 0
    if window_handle <= 0:
        raise RuntimeError("The active WindowHub window has no usable top-level handle.")

    try:
        foreground_handle = int(ctypes.windll.user32.GetForegroundWindow())
        foreground_owner = (
            int(ctypes.windll.user32.GetAncestor(foreground_handle, 3))
            if foreground_handle > 0
            else 0
        )
    except Exception:
        foreground_handle = 0
        foreground_owner = 0
    focused = foreground_handle > 0 and foreground_handle == window_handle

    # Build only the minimum observation expected by the existing UIA provider.
    # This path does not instantiate the RobotGUIExecutor or any action engine,
    # and does not capture/save screenshots.
    from app.agent.environment.environment_observation import EnvironmentObservation
    from app.agent.environment.environment_state import EnvironmentState
    from app.agent.perception.perception_engine import PerceptionEngine
    from app.agent.perception.windows_ui_automation_provider import WindowsUIAutomationProvider
    from app.runtime.execution.window.window_rect import WindowRect

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowsDesktop",
            active_window_title=title or None,
        ),
        metadata={
            "source": "windowhub_read_only_diagnostic",
            "window_rect": WindowRect(left=left, top=top, width=width, height=height),
            "window_handle": window_handle,
            "window_focused": focused,
            "foreground_window_handle": foreground_handle if foreground_handle > 0 else None,
            "foreground_root_owner_handle": foreground_owner if foreground_owner > 0 else None,
        },
    )
    scene = PerceptionEngine(
        providers=(WindowsUIAutomationProvider(),),
    ).perceive(observation)
    return scene, title or None, focused, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inventory of the active WindowHub semantic UI. "
            "This diagnostic never plans or executes actions."
        )
    )
    parser.add_argument(
        "--max-elements",
        type=int,
        default=100,
        help="Maximum semantic elements to print (1..500, default: 100).",
    )
    parser.add_argument(
        "--include-sensitive-values",
        action="store_true",
        help=(
            "Explicitly include current field values, active window title, document name, "
            "and raw document scopes. These may contain customer/business data."
        ),
    )
    args = parser.parse_args()

    try:
        scene, title, focused, stop_reason = observe_windowhub_scene()
        report = build_read_only_report(
            scene,
            active_window_title=title,
            window_focused=focused,
            include_sensitive_values=args.include_sensitive_values,
            max_elements=args.max_elements,
            stop_reason=stop_reason,
        )
    except Exception as exc:
        print(json.dumps({
            "diagnostic": "windowhub_read_only_semantic_inventory",
            "mode": "READ_ONLY",
            "computer_actions_executed": False,
            "network_calls_made": False,
            "files_written": False,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": "The read-only inventory failed before completion. No computer action was attempted.",
        }, ensure_ascii=False, indent=2))
        return 2

    report["ok"] = stop_reason is None
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if stop_reason is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
