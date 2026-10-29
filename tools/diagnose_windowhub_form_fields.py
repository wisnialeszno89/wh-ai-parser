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
    if kind != "button":
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


def build_field_report(
    descendants: list[object],
    *,
    active_window_title: str,
    max_fields: int = 200,
) -> dict[str, Any]:
    """Build a redacted report from existing UIA wrappers; no actions are run."""
    text_entries: list[dict[str, Any]] = []
    for item in descendants:
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

    fields: list[dict[str, Any]] = []
    all_field_count = 0
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
            "index": all_field_count + 1,
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
        all_field_count += 1
        if len(fields) >= max_fields:
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
        "static_text_count": len(text_entries),
        "field_count": all_field_count,
        "fields_reported": len(fields),
        "truncated": all_field_count >= max_fields,
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

        window, stop_reason = _select_target_window(
            gw.getAllWindows(),
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
        root_spec = Desktop(backend="uia").window(handle=handle)
        wrapper = getattr(root_spec, "wrapper_object", None)
        root = wrapper() if callable(wrapper) else root_spec
        descendants = list(root.descendants())
        report = build_field_report(
            descendants,
            active_window_title=(getattr(window, "title", "") or "").strip(),
            max_fields=args.max_fields,
        )
        report["ok"] = True
        report["window_title_matches_selector"] = (
            args.window_title_contains.casefold()
            in (getattr(window, "title", "") or "").casefold()
        )
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
