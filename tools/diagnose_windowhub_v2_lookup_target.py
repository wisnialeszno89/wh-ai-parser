"""Read-only UIA diagnostics for the WindowHub lookup target.

Reads only structural UIA properties: control type, class name, automation-id
match booleans, visibility, enabled state, and bounds presence. A window
caption is compared to a fixed prefix internally; its text is never output.
No control names/values, table headers/cells, clicks, focus changes, or
pattern invocations are performed.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import sys
from collections import Counter


LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
GRID_AUTOMATION_ID = "PART_GridControl"
WINDOWHUB_TITLE_PREFIX = "Okna -"


def _string(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _rect_nonempty(item: object) -> bool:
    try:
        rect = item.rectangle()
        return int(rect.width()) > 0 and int(rect.height()) > 0
    except Exception:
        return False


def _ancestor_roles(item: object, max_depth: int = 5) -> list[str]:
    roles: list[str] = []
    current = item
    for _ in range(max_depth):
        parent_getter = getattr(current, "parent", None)
        if not callable(parent_getter):
            break
        try:
            current = parent_getter()
            if current is None:
                break
            role = _string(
                getattr(current.element_info, "control_type", "")
            ).casefold()
            if role:
                roles.append(role)
        except Exception:
            break
    return roles


def _window_area(window: object) -> int:
    try:
        rect = window.rectangle()
        return max(0, int(rect.width())) * max(0, int(rect.height()))
    except Exception:
        return 0


def _inspect_root(window: object) -> dict:
    try:
        root_info = window.element_info
        root_role = _string(
            getattr(root_info, "control_type", None)
        ).casefold() or None
        root_class = _string(
            getattr(root_info, "class_name", None)
        ).casefold() or None
    except Exception:
        root_role = None
        root_class = None

    try:
        descendants = tuple(window.descendants())
        scan_error = None
    except Exception as exc:
        descendants = ()
        scan_error = type(exc).__name__

    role_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    candidates: list[dict] = []
    exact_lookup_count = 0
    lookup_class_count = 0
    exact_grid_count = 0

    for item in descendants:
        try:
            info = item.element_info
            automation_id = _string(getattr(info, "automation_id", None))
            role = _string(getattr(info, "control_type", None)).casefold()
            class_name = _string(getattr(info, "class_name", None)).casefold()
            visible = bool(getattr(info, "visible", True))
            enabled = bool(getattr(info, "enabled", False))
        except Exception:
            continue

        if role:
            role_counts[role] += 1
        if class_name:
            class_counts[class_name] += 1

        is_lookup_id = automation_id == LOOKUP_AUTOMATION_ID
        is_lookup_class = "lookupedit" in class_name
        is_grid_id = automation_id == GRID_AUTOMATION_ID
        if is_lookup_id:
            exact_lookup_count += 1
        if is_lookup_class:
            lookup_class_count += 1
        if is_grid_id and role == "datagrid":
            exact_grid_count += 1

        if is_lookup_id or is_lookup_class or is_grid_id:
            candidates.append(
                {
                    "expected_lookup_id_match": is_lookup_id,
                    "lookupedit_class_match": is_lookup_class,
                    "expected_grid_id_match": is_grid_id,
                    "control_type": role or None,
                    "visible": visible,
                    "enabled": enabled,
                    "nonempty_bounds": _rect_nonempty(item),
                    "ancestor_control_types": _ancestor_roles(item),
                }
            )

    candidates.sort(
        key=lambda item: (
            not item["expected_lookup_id_match"],
            not item["lookupedit_class_match"],
            not item["expected_grid_id_match"],
        )
    )
    return {
        "root_control_type": root_role,
        "root_class_name": root_class,
        "window_area_pixels": _window_area(window),
        "descendant_count": len(descendants),
        "scan_error": scan_error,
        "exact_lookup_id_count": exact_lookup_count,
        "lookupedit_class_count": lookup_class_count,
        "exact_grid_id_datagrid_count": exact_grid_count,
        "control_type_counts": dict(sorted(role_counts.items())),
        "most_common_class_names": dict(class_counts.most_common(12)),
        "structural_candidates": candidates[:12],
    }


def _foreground_related(window_handle: int) -> bool:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_foreground = user32.GetForegroundWindow
    get_foreground.argtypes = ()
    get_foreground.restype = ctypes.wintypes.HWND
    get_ancestor = user32.GetAncestor
    get_ancestor.argtypes = (ctypes.wintypes.HWND, ctypes.wintypes.UINT)
    get_ancestor.restype = ctypes.wintypes.HWND

    foreground = int(get_foreground() or 0)
    if not foreground:
        return False
    hwnd = ctypes.wintypes.HWND(foreground)
    root = int(get_ancestor(hwnd, 2) or 0)
    root_owner = int(get_ancestor(hwnd, 3) or 0)
    return window_handle in {foreground, root, root_owner}


def main() -> int:
    if os.name != "nt":
        print(json.dumps({"result": "FAIL", "reason": "requires_windows"}))
        return 2

    sys.coinit_flags = 2
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        windows = tuple(desktop.windows())
        roots = []
        for index, window in enumerate(windows):
            try:
                handle = int(window.handle)
                # The caption is used only for a fixed-prefix boolean; it is
                # never printed, stored, or passed to any external service.
                try:
                    caption = _string(window.window_text())
                    title_prefix_match = (
                        caption.casefold().startswith(
                            WINDOWHUB_TITLE_PREFIX.casefold()
                        )
                    )
                except Exception:
                    title_prefix_match = False

                data = _inspect_root(window)
                data["top_level_window_index"] = index
                data["windowhub_title_prefix_match"] = title_prefix_match
                data["foreground_related_to_root"] = (
                    _foreground_related(handle) if handle > 0 else False
                )
                roots.append(data)
            except Exception as exc:
                roots.append(
                    {
                        "top_level_window_index": index,
                        "root_inspection_error": type(exc).__name__,
                    }
                )

        roots.sort(
            key=lambda item: (
                not item.get("windowhub_title_prefix_match", False),
                not bool(
                    item.get("exact_lookup_id_count", 0)
                    or item.get("lookupedit_class_count", 0)
                    or item.get("exact_grid_id_datagrid_count", 0)
                ),
                -int(item.get("window_area_pixels", 0)),
            )
        )
        title_match_count = sum(
            bool(item.get("windowhub_title_prefix_match"))
            for item in roots
        )
        structural_match_count = sum(
            bool(
                item.get("exact_lookup_id_count", 0)
                or item.get("lookupedit_class_count", 0)
                or item.get("exact_grid_id_datagrid_count", 0)
            )
            for item in roots
        )
        result = {
            "result": "DIAGNOSTIC_ONLY",
            "top_level_window_count": len(windows),
            "windowhub_title_prefix_match_count": title_match_count,
            "windows_with_any_expected_structural_match": (
                structural_match_count
            ),
            "windows": roots[:12],
            "privacy": {
                "window_captions_read_for_prefix_match_only": True,
                "window_captions_output": False,
                "control_names_or_values_read": False,
                "table_headers_or_cells_read": False,
                "clicks_or_invocations": 0,
                "focus_changes": 0,
                "record_selection": False,
                "offer_changes": False,
            },
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "result": "FAIL",
                    "error_type": type(exc).__name__,
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
