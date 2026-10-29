"""Read-only WindowHub form-field context diagnostic.

Reports editable UI Automation controls, nearby static-text label candidates,
control identifiers, ancestor context, and value availability flags only.
It never prints input values, clicks, types, saves, captures screenshots, or
writes local files.
"""
from __future__ import annotations

import argparse
import ctypes
import json
from collections import Counter
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.diagnose_windowhub_semantics import (  # noqa: E402
    _select_target_window,
    _window_process_name,
    observe_windowhub_scene,
)

EDITABLE_TYPES = frozenset(
    {"edit", "combobox", "checkbox", "radiobutton", "listitem", "treeitem"}
)
EDITOR_HINTS = (
    "lookup",
    "dateedit",
    "combobox",
    "textedit",
    "spinedit",
    "buttonedit",
    "layoutitem",
)


def _string_attr(obj: object, name: str) -> str:
    try:
        value = getattr(obj, name, None)
    except Exception:
        return ""
    return value.strip() if isinstance(value, str) else ""


def _bool_attr(obj: object, name: str) -> bool | None:
    try:
        value = getattr(obj, name, None)
    except Exception:
        return None
    return value if isinstance(value, bool) else None


def _rect(item: object) -> tuple[int, int, int, int] | None:
    try:
        rectangle = item.rectangle()
        left = int(rectangle.left)
        top = int(rectangle.top)
        width = int(rectangle.width())
        height = int(rectangle.height())
    except Exception:
        return None
    if width <= 0 or height <= 0:
        return None
    return left, top, width, height


def _is_field_candidate(
    control_type: str,
    name: str,
    automation_id: str,
    class_name: str,
) -> bool:
    kind = control_type.strip().casefold()
    if kind in EDITABLE_TYPES:
        return True
    # Some WindowHub/DevExpress editors appear as generic Custom controls or
    # buttons. For this read-only diagnostic, include them only when a known
    # editor hint appears in their name, AutomationId, or class.
    if kind not in {"button", "custom", "unknown"}:
        return False
    searchable = " ".join((name, automation_id, class_name)).casefold()
    return any(hint in searchable for hint in EDITOR_HINTS)


def _rank_label_candidates(
    field_bounds: tuple[int, int, int, int],
    text_entries: list[dict[str, Any]],
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Rank nearby text nodes likely to describe a field, without guessing."""
    field_left, field_top, field_width, field_height = field_bounds
    field_center_y = field_top + field_height / 2
    ranked: list[tuple[float, dict[str, Any]]] = []

    for entry in text_entries:
        label = entry.get("label")
        bounds = entry.get("bounds")
        if not isinstance(label, str) or not label.strip():
            continue
        if not isinstance(bounds, (tuple, list)) or len(bounds) != 4:
            continue
        try:
            text_left, text_top, text_width, text_height = (
                int(value) for value in bounds
            )
        except (TypeError, ValueError):
            continue

        text_center_y = text_top + text_height / 2
        vertical_distance = abs(field_center_y - text_center_y)
        horizontal_distance = field_left - (text_left + text_width)
        if vertical_distance > 80 or horizontal_distance < -20 or horizontal_distance > 350:
            continue

        score = vertical_distance + max(horizontal_distance, 0) * 0.25
        ranked.append(
            (
                score,
                {
                    "label": label.strip(),
                    "vertical_distance_px": round(vertical_distance, 1),
                    "horizontal_gap_px": round(horizontal_distance, 1),
                    "score": round(score, 1),
                },
            )
        )

    ranked.sort(key=lambda pair: (pair[0], pair[1]["label"].casefold()))
    return [candidate for _, candidate in ranked[: max(0, limit)]]


def _value_flags(item: object) -> tuple[bool, bool]:
    """Return value-availability and nonempty flags; never return the value."""
    try:
        value = getattr(item.element_info, "rich_text", None)
    except Exception:
        value = None
    if isinstance(value, str):
        return True, bool(value.strip())

    try:
        getter = getattr(item, "get_value", None)
        value = getter() if callable(getter) else None
    except Exception:
        value = None
    if isinstance(value, str):
        return True, bool(value.strip())
    return False, False


def _checked_state(item: object) -> bool | None:
    for attribute in ("is_checked", "get_toggle_state"):
        try:
            getter = getattr(item, attribute, None)
            value = getter() if callable(getter) else None
            if isinstance(value, bool):
                return value
            if isinstance(value, int) and value in (0, 1):
                return bool(value)
        except Exception:
            continue
    return None


def _ancestor_context(item: object, *, limit: int = 3) -> list[dict[str, str]]:
    ancestors: list[dict[str, str]] = []
    current = item
    for _ in range(limit):
        try:
            parent_getter = getattr(current, "parent", None)
            current = parent_getter() if callable(parent_getter) else None
        except Exception:
            current = None
        if current is None:
            break
        try:
            info = current.element_info
        except Exception:
            break
        ancestors.append(
            {
                "name": _string_attr(info, "name"),
                "kind": _string_attr(info, "control_type").casefold(),
                "class_name": _string_attr(info, "class_name"),
                "automation_id": _string_attr(info, "automation_id"),
            }
        )
    return ancestors


def _is_owned_window_candidate(
    candidate_handle: int,
    root_handle: int,
    candidate_root_owner: int,
) -> bool:
    """Accept only a distinct top-level window whose root owner is the target app."""
    return (
        candidate_handle > 0
        and root_handle > 0
        and candidate_handle != root_handle
        and candidate_root_owner == root_handle
    )


def build_field_report(
    descendants: list[object],
    *,
    active_window_title: str,
    max_fields: int = 200,
    owned_window_descendants: list[list[object]] | None = None,
) -> dict[str, Any]:
    """Build a redacted report, preserving window boundaries for label matching."""
    groups: list[tuple[str, list[object]]] = [("application_window", descendants)]
    for index, owned_descendants in enumerate(owned_window_descendants or [], start=1):
        groups.append((f"owned_window_{index}", owned_descendants))

    fields: list[dict[str, Any]] = []
    static_text_count = 0
    scanned_windows: list[dict[str, Any]] = []
    hit_field_limit = False

    for window_scope, group_descendants in groups:
        text_entries: list[dict[str, Any]] = []
        for item in group_descendants:
            try:
                info = item.element_info
                control_type = _string_attr(info, "control_type").casefold()
                label = _string_attr(info, "name")
            except Exception:
                continue
            if control_type != "text" or not label:
                continue
            bounds = _rect(item)
            if bounds is not None:
                text_entries.append({"label": label, "bounds": bounds})

        static_text_count += len(text_entries)
        scanned_windows.append({
            "scope": window_scope,
            "descendant_count": len(group_descendants),
            "static_text_count": len(text_entries),
        })

        for item in group_descendants:
            try:
                info = item.element_info
                control_type = _string_attr(info, "control_type").casefold()
                name = _string_attr(info, "name")
                automation_id = _string_attr(info, "automation_id")
                class_name = _string_attr(info, "class_name")
            except Exception:
                continue
            if not _is_field_candidate(control_type, name, automation_id, class_name):
                continue

            bounds = _rect(item)
            if bounds is None:
                continue
            try:
                enabled_value = getattr(info, "enabled", None)
                enabled = enabled_value if isinstance(enabled_value, bool) else None
            except Exception:
                enabled = None
            try:
                visible_value = getattr(info, "visible", None)
                visible = visible_value if isinstance(visible_value, bool) else None
            except Exception:
                visible = None

            value_available, value_nonempty = _value_flags(item)
            entry: dict[str, Any] = {
                "index": len(fields) + 1,
                "window_scope": window_scope,
                "name": name or "<unnamed>",
                "kind": control_type or "unknown",
                "automation_id": automation_id,
                "class_name": class_name,
                "enabled": enabled,
                "visible": visible,
                "bounds": {
                    "left": bounds[0],
                    "top": bounds[1],
                    "width": bounds[2],
                    "height": bounds[3],
                },
                "value_available": value_available,
                "value_nonempty": value_nonempty,
                "checked_state": _checked_state(item) if control_type == "checkbox" else None,
                "nearby_text_candidates": _rank_label_candidates(bounds, text_entries),
                "ancestors": _ancestor_context(item),
            }
            fields.append(entry)
            if len(fields) >= max_fields:
                hit_field_limit = True
                break

        if hit_field_limit:
            break

    return {
        "diagnostic": "windowhub_read_only_form_field_context",
        "mode": "READ_ONLY",
        "computer_actions_executed": False,
        "network_calls_made": False,
        "files_written": False,
        "screenshot_saved": False,
        "window_title": "<redacted>",
        "window_title_matches_selector": bool(active_window_title),
        "static_text_count": static_text_count,
        "field_count": len(fields),
        "fields_reported": len(fields),
        "truncated": hit_field_limit,
        "scanned_windows": scanned_windows,
        "owned_windows_scanned": max(0, len(groups) - 1),
        "fields": fields,
        "safety_note": (
            "Current field values and window/document names are not printed. "
            "Control and nearby label names may still contain business data; inspect before sharing."
        ),
    }


def _runtime_id(item: object) -> str | None:
    try:
        value = getattr(item.element_info, "runtime_id", None)
    except Exception:
        return None
    if isinstance(value, (tuple, list)):
        return "-".join(str(part) for part in value)
    return value if isinstance(value, str) and value else None


def build_semantic_field_report(
    scene: object,
    raw_descendant_groups: list[tuple[int, list[object]]],
    *,
    root_bounds: tuple[int, int, int, int],
    root_handle: int,
    active_window_title: str,
    max_fields: int = 200,
) -> dict[str, Any]:
    """Report fields from the canonical perception provider, not raw UIA roles."""
    origin_x, origin_y, _, _ = root_bounds
    text_entries_by_handle: dict[int, list[dict[str, Any]]] = {}
    raw_lookup: dict[str, object] = {}
    raw_control_types: Counter[str] = Counter()
    raw_descendant_count = 0

    for window_handle, descendants in raw_descendant_groups:
        text_entries: list[dict[str, Any]] = []
        for item in descendants:
            try:
                info = item.element_info
                control_type = _string_attr(info, "control_type").casefold()
                label = _string_attr(info, "name")
            except Exception:
                continue

            raw_control_types[control_type or "<unknown>"] += 1
            raw_descendant_count += 1
            runtime_id = _runtime_id(item)
            if runtime_id:
                raw_lookup[runtime_id] = item

            if control_type != "text" or not label:
                continue
            bounds = _rect(item)
            if bounds is not None:
                text_entries.append({"label": label, "bounds": bounds})
        text_entries_by_handle[int(window_handle)] = text_entries

    semantic_elements = tuple(getattr(scene, "elements", ()) or ())
    semantic_kinds: Counter[str] = Counter()
    fields: list[dict[str, Any]] = []
    truncated = False

    for element in semantic_elements:
        kind_value = getattr(element, "kind", "unknown")
        kind = str(getattr(kind_value, "value", kind_value) or "unknown").casefold()
        label = str(getattr(element, "label", "") or "").strip()
        metadata = getattr(element, "metadata", None) or {}
        if not isinstance(metadata, dict):
            metadata = {}

        semantic_kinds[kind] += 1
        automation_id = str(metadata.get("automation_id") or "")
        class_name = str(metadata.get("uia_class_name") or "")
        if not _is_field_candidate(kind, label, automation_id, class_name):
            continue

        x = getattr(element, "x", None)
        y = getattr(element, "y", None)
        width = getattr(element, "width", None)
        height = getattr(element, "height", None)
        try:
            bounds = (
                origin_x + int(x),
                origin_y + int(y),
                int(width),
                int(height),
            )
        except (TypeError, ValueError):
            continue
        if bounds[2] <= 0 or bounds[3] <= 0:
            continue

        runtime_id = metadata.get("uia_runtime_id")
        if isinstance(runtime_id, (tuple, list)):
            runtime_id = "-".join(str(part) for part in runtime_id)
        raw_item = raw_lookup.get(runtime_id) if isinstance(runtime_id, str) else None
        if raw_item is not None and not class_name:
            class_name = _string_attr(raw_item.element_info, "class_name")

        try:
            source_handle = int(metadata.get("uia_window_handle") or root_handle)
        except (TypeError, ValueError):
            source_handle = root_handle
        # Keep nearby-label matching within the same top-level window.
        text_entries = text_entries_by_handle.get(source_handle, [])

        current_value = metadata.get("current_value")
        value_available = isinstance(current_value, str)
        value_nonempty = bool(current_value.strip()) if value_available else False

        fields.append({
            "index": len(fields) + 1,
            "window_scope": (
                "owned_window"
                if metadata.get("uia_owned_modal") is True
                else "application_window"
            ),
            "name": label or "<unnamed>",
            "kind": kind,
            "automation_id": automation_id,
            "class_name": class_name,
            "enabled": metadata.get("uia_enabled"),
            "visible": metadata.get("uia_visible"),
            "bounds": {
                "left": bounds[0],
                "top": bounds[1],
                "width": bounds[2],
                "height": bounds[3],
            },
            "value_available": value_available,
            "value_nonempty": value_nonempty,
            "checked_state": _checked_state(raw_item) if raw_item is not None and kind == "checkbox" else None,
            "nearby_text_candidates": _rank_label_candidates(bounds, text_entries),
            "ancestors": _ancestor_context(raw_item) if raw_item is not None else [],
        })
        if len(fields) >= max_fields:
            truncated = True
            break

    # The canonical semantic scene includes a separate WindowHub dialog only
    # when that dialog is the foreground owned window at observation time.
    # Running this diagnostic from PowerShell may make PowerShell foreground,
    # even though the WindowHub dialog remains visible. Raw descendant groups
    # above are collected independently from visible HWNDs owned by WindowHub,
    # so use them as a clearly marked, read-only fallback for those windows.
    semantic_owned_handles: set[int] = set()
    for element in semantic_elements:
        metadata = getattr(element, "metadata", None) or {}
        if not isinstance(metadata, dict) or metadata.get("uia_owned_modal") is not True:
            continue
        try:
            element_handle = int(metadata.get("uia_window_handle") or 0)
        except (TypeError, ValueError):
            continue
        if element_handle > 0:
            semantic_owned_handles.add(element_handle)

    owned_window_index = 0
    raw_owned_fallback_field_count = 0
    for window_handle, descendants in raw_descendant_groups:
        try:
            group_handle = int(window_handle)
        except (TypeError, ValueError):
            continue
        if group_handle <= 0 or group_handle == root_handle:
            continue
        owned_window_index += 1
        if group_handle in semantic_owned_handles:
            # The dialog was already represented by semantic perception. Do
            # not duplicate its fields with raw candidates.
            continue

        text_entries = text_entries_by_handle.get(group_handle, [])
        for item in descendants:
            try:
                info = item.element_info
                control_type = _string_attr(info, "control_type").casefold()
                name = _string_attr(info, "name")
                automation_id = _string_attr(info, "automation_id")
                class_name = _string_attr(info, "class_name")
            except Exception:
                continue
            if not _is_field_candidate(control_type, name, automation_id, class_name):
                continue

            bounds = _rect(item)
            if bounds is None:
                continue
            enabled = _bool_attr(info, "enabled")
            visible = _bool_attr(info, "visible")
            value_available, value_nonempty = _value_flags(item)

            fields.append({
                "index": len(fields) + 1,
                "window_scope": "owned_window",
                "owned_window_index": owned_window_index,
                "source": "raw_uia_owned_window_fallback",
                "name": name or "<unnamed>",
                "kind": control_type or "unknown",
                "automation_id": automation_id,
                "class_name": class_name,
                "enabled": enabled,
                "visible": visible,
                "bounds": {
                    "left": bounds[0],
                    "top": bounds[1],
                    "width": bounds[2],
                    "height": bounds[3],
                },
                "value_available": value_available,
                "value_nonempty": value_nonempty,
                "checked_state": _checked_state(item) if control_type == "checkbox" else None,
                "nearby_text_candidates": _rank_label_candidates(bounds, text_entries),
                "ancestors": _ancestor_context(item),
            })
            raw_owned_fallback_field_count += 1
            if len(fields) >= max_fields:
                truncated = True
                break

        if len(fields) >= max_fields:
            truncated = True
            break

    return {
        "diagnostic": "windowhub_read_only_form_field_context",
        "mode": "READ_ONLY",
        "computer_actions_executed": False,
        "network_calls_made": False,
        "files_written": False,
        "screenshot_saved": False,
        "window_title": "<redacted>",
        "window_title_matches_selector": bool(active_window_title),
        "raw_descendant_count": raw_descendant_count,
        "static_text_count": sum(len(items) for items in text_entries_by_handle.values()),
        "semantic_element_count": len(semantic_elements),
        "raw_owned_window_fallback_field_count": raw_owned_fallback_field_count,
        "raw_control_type_counts": dict(sorted(raw_control_types.items())),
        "semantic_kind_counts": dict(sorted(semantic_kinds.items())),
        "field_count": len(fields),
        "fields_reported": len(fields),
        "truncated": truncated,
        "fields": fields,
        "safety_note": (
            "Current field values and window/document names are not printed. "
            "Control and nearby label names may still contain business data; inspect before sharing."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only WindowHub field context inventory. No computer actions are executed."
    )
    parser.add_argument(
        "--window-title-contains",
        default="Okna -",
        help="Unique visible top-level window title fragment (default: Okna -).",
    )
    parser.add_argument(
        "--process-name",
        default=None,
        help="Optional exact executable stem, for example Okna or Okna.exe.",
    )
    parser.add_argument(
        "--window-handle",
        type=lambda value: int(value, 0),
        default=None,
        help="Optional exact decimal or 0x-prefixed HWND; requires --process-name.",
    )
    parser.add_argument("--max-fields", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if os.name != "nt":
        print(json.dumps({
            "diagnostic": "windowhub_read_only_form_field_context",
            "mode": "READ_ONLY",
            "ok": False,
            "error": "This diagnostic must be run on Windows.",
            "computer_actions_executed": False,
        }, ensure_ascii=True, indent=2))
        return 2
    if not 1 <= args.max_fields <= 500:
        raise SystemExit("--max-fields must be between 1 and 500.")
    if args.window_handle is not None and not args.process_name:
        raise SystemExit("--window-handle requires --process-name.")

    try:
        import pygetwindow as gw
        from pywinauto import Desktop
        from app.agent.platform.windows_com import ensure_windows_sta

        def is_visible(handle: int) -> bool:
            return bool(ctypes.windll.user32.IsWindowVisible(int(handle)))

        all_windows = gw.getAllWindows()
        window, stop_reason = _select_target_window(
            all_windows,
            title_contains=args.window_title_contains,
            process_name=args.process_name,
            window_handle=args.window_handle,
            process_name_checker=_window_process_name if args.process_name else None,
            visibility_checker=is_visible,
        )
        if window is None:
            print(json.dumps({
                "diagnostic": "windowhub_read_only_form_field_context",
                "mode": "READ_ONLY",
                "ok": False,
                "observation_skipped_reason": stop_reason,
                "computer_actions_executed": False,
                "network_calls_made": False,
                "files_written": False,
            }, ensure_ascii=True, indent=2))
            return 2

        handle = int(getattr(window, "_hWnd", 0) or 0)
        ensure_windows_sta()
        desktop = Desktop(backend="uia")
        root_spec = desktop.window(handle=handle)
        wrapper = getattr(root_spec, "wrapper_object", None)
        root = wrapper() if callable(wrapper) else root_spec
        descendants = list(root.descendants())

        # WindowHub forms can live in a separate owned top-level dialog.
        # Discover all visible owned windows, not only the foreground window:
        # launching this read-only command from PowerShell may itself change
        # the foreground window even while the dialog remains open.
        owned_window_groups: list[list[object]] = []
        owned_window_handles: list[int] = []
        for candidate in all_windows:
            try:
                candidate_handle = int(getattr(candidate, "_hWnd", 0) or 0)
                candidate_width = int(getattr(candidate, "width", 0) or 0)
                candidate_height = int(getattr(candidate, "height", 0) or 0)
                minimized = getattr(candidate, "isMinimized", False)
                if callable(minimized):
                    minimized = minimized()
            except Exception:
                continue

            if (
                candidate_handle <= 0
                or candidate_width <= 0
                or candidate_height <= 0
                or minimized is True
                or not is_visible(candidate_handle)
            ):
                continue

            try:
                candidate_root_owner = int(
                    ctypes.windll.user32.GetAncestor(candidate_handle, 3)
                )
            except Exception:
                continue

            if not _is_owned_window_candidate(
                candidate_handle,
                handle,
                candidate_root_owner,
            ):
                continue
            if candidate_handle in owned_window_handles:
                continue

            try:
                candidate_spec = desktop.window(handle=candidate_handle)
                candidate_wrapper = getattr(candidate_spec, "wrapper_object", None)
                candidate_root = (
                    candidate_wrapper()
                    if callable(candidate_wrapper)
                    else candidate_spec
                )
                candidate_descendants = list(candidate_root.descendants())
            except Exception:
                continue

            owned_window_handles.append(candidate_handle)
            owned_window_groups.append(candidate_descendants)

        # Reuse the same semantic perception provider that already reports
        # WindowHub's editor controls as edit/combobox/checkbox. Raw pywinauto
        # roles can differ for DevExpress/WPF editor wrappers.
        scene, scene_title, scene_focused, scene_stop_reason = observe_windowhub_scene(
            window_title_contains=args.window_title_contains,
            process_name=args.process_name,
            window_handle=args.window_handle,
        )
        if scene is None:
            print(json.dumps({
                "diagnostic": "windowhub_read_only_form_field_context",
                "mode": "READ_ONLY",
                "ok": False,
                "observation_skipped_reason": scene_stop_reason,
                "computer_actions_executed": False,
                "network_calls_made": False,
                "files_written": False,
            }, ensure_ascii=True, indent=2))
            return 2

        semantic_raw_groups = [(handle, list(descendants))]
        semantic_raw_groups.extend(
            (owned_handle, list(group))
            for owned_handle, group in zip(owned_window_handles, owned_window_groups)
        )

        report = build_semantic_field_report(
            scene,
            semantic_raw_groups,
            root_bounds=(int(window.left), int(window.top), int(window.width), int(window.height)),
            root_handle=handle,
            active_window_title=scene_title or (getattr(window, "title", "") or "").strip(),
            max_fields=args.max_fields,
        )
        report["ok"] = True
        report["window_title_matches_selector"] = (
            args.window_title_contains.casefold()
            in (getattr(window, "title", "") or "").casefold()
        )
        report["window_context"] = {
            "application_window_scanned": True,
            "owned_window_handles_scanned": len(owned_window_handles),
        }
        report["target_selection"] = {
            "mode": "window_handle" if args.window_handle is not None
                else ("process_name" if args.process_name else "window_title"),
            "selector": (
                f"0x{args.window_handle:X}" if args.window_handle is not None
                else (args.process_name or args.window_title_contains)
            ),
            "target_matched": True,
        }
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "diagnostic": "windowhub_read_only_form_field_context",
            "mode": "READ_ONLY",
            "ok": False,
            "error_type": type(exc).__name__,
            "error": "Field inventory failed. No computer action was attempted.",
            "computer_actions_executed": False,
            "network_calls_made": False,
            "files_written": False,
        }, ensure_ascii=True, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
