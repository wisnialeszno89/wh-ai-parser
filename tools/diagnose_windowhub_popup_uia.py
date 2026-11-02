"""Read-only inspection of WindowHub-owned popup/list windows.

The diagnostic scans same-process top-level windows, focusing on combo/list/
popup classes and windows whose Win32 root owner is WindowHub. For each
candidate it reports only class names, visibility, bounds, control-type and
class-name counts, and boolean matches for known AutomationIds.

It never reads UIA Name/Value/text, customer values, table headers/cells,
raw HWNDs, or native control IDs. No click, focus change, pattern invocation,
or application-state mutation is performed.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.diagnose_windowhub_win32_children import (
    GA_ROOTOWNER,
    _class_name,
    _configure_api,
    _enumerate_process_top_windows,
    _find_windowhub_root,
    _hwnd_value,
    _rect_nonempty,
)


LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
GRID_AUTOMATION_ID = "PART_GridControl"
POPUP_CLASS_TOKENS = (
    "combo",
    "list",
    "lookup",
    "grid",
    "popup",
    "32768",
)


def _normalize(value: object) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _is_popup_candidate(class_name: str, *, owner_matches: bool, visible: bool) -> bool:
    normalized = class_name.casefold()
    class_match = any(token in normalized for token in POPUP_CLASS_TOKENS)
    return class_match or (owner_matches and visible)


def _inspect_uia_subtree(desktop, hwnd: int) -> dict:
    try:
        wrapper = desktop.window(handle=hwnd).wrapper_object()
        descendants = tuple(wrapper.descendants())
    except Exception as exc:
        return {
            "uia_scan_status": f"failed:{type(exc).__name__}",
            "uia_descendant_count": 0,
            "control_type_counts": {},
            "class_name_counts": {},
            "expected_lookup_automation_id_count": 0,
            "expected_grid_automation_id_count": 0,
            "lookupedit_class_count": 0,
            "datagrid_control_type_count": 0,
            "table_control_type_count": 0,
        }

    roles: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    lookup_id_count = 0
    grid_id_count = 0
    lookup_class_count = 0
    datagrid_count = 0
    table_count = 0

    for item in descendants:
        try:
            info = item.element_info
            automation_id = _normalize(
                getattr(info, "automation_id", None)
            )
            control_type = _normalize(
                getattr(info, "control_type", None)
            )
            class_name = _normalize(
                getattr(info, "class_name", None)
            )
        except Exception:
            continue

        if control_type:
            roles[control_type] += 1
        if class_name:
            classes[class_name] += 1

        lookup_id_count += int(
            automation_id == LOOKUP_AUTOMATION_ID.casefold()
        )
        grid_id_count += int(
            automation_id == GRID_AUTOMATION_ID.casefold()
        )
        lookup_class_count += int("lookupedit" in class_name)
        datagrid_count += int(control_type == "datagrid")
        table_count += int(control_type == "table")

    return {
        "uia_scan_status": "ok",
        "uia_descendant_count": len(descendants),
        "control_type_counts": dict(sorted(roles.items())),
        "class_name_counts": dict(sorted(classes.items())),
        "expected_lookup_automation_id_count": lookup_id_count,
        "expected_grid_automation_id_count": grid_id_count,
        "lookupedit_class_count": lookup_class_count,
        "datagrid_control_type_count": datagrid_count,
        "table_control_type_count": table_count,
    }


def _inspect_popup_candidates(api, enum_proc, desktop, root_hwnd: int, process_id: int):
    top_windows = _enumerate_process_top_windows(
        api,
        enum_proc,
        process_id,
    )
    candidates = []

    for hwnd in top_windows:
        class_name = _class_name(api, hwnd)
        visible = bool(api.IsWindowVisible(hwnd))
        owner = _hwnd_value(api.GetAncestor(hwnd, GA_ROOTOWNER))
        owner_matches = owner == root_hwnd

        if not _is_popup_candidate(
            class_name,
            owner_matches=owner_matches,
            visible=visible,
        ):
            continue

        ui = _inspect_uia_subtree(desktop, hwnd)
        candidates.append(
            {
                "native_class_name": class_name,
                "visible": visible,
                "nonempty_bounds": _rect_nonempty(api, hwnd),
                "root_owner_matches_windowhub": owner_matches,
                **ui,
            }
        )

    candidates.sort(
        key=lambda item: (
            not item["visible"],
            not item["root_owner_matches_windowhub"],
            item["native_class_name"],
        )
    )
    return len(top_windows), candidates


def main() -> int:
    if os.name != "nt":
        print(json.dumps({"result": "FAIL", "reason": "requires_windows"}))
        return 2

    try:
        sys.coinit_flags = 2
        from pywinauto import Desktop

        api, enum_proc = _configure_api()
        desktop = Desktop(backend="uia")
        root = _find_windowhub_root(desktop)
        root_hwnd = _hwnd_value(root.handle)
        if root_hwnd <= 0:
            raise RuntimeError("windowhub_root_handle_invalid")

        process_id = ctypes.wintypes.DWORD()
        api.GetWindowThreadProcessId(
            root_hwnd,
            ctypes.byref(process_id),
        )
        if process_id.value == 0:
            raise RuntimeError("windowhub_process_id_unavailable")

        process_window_count, candidates = _inspect_popup_candidates(
            api,
            enum_proc,
            desktop,
            root_hwnd,
            int(process_id.value),
        )

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "windowhub_process_top_window_count": process_window_count,
            "popup_candidate_count": len(candidates),
            "visible_popup_candidate_count": sum(
                bool(item["visible"]) for item in candidates
            ),
            "popup_candidates": candidates[:40],
            "privacy": {
                "window_caption_compared_to_fixed_prefix_only": True,
                "window_captions_output": False,
                "uia_name_or_value_read": False,
                "customer_text_or_values_read": False,
                "table_headers_or_cells_read": False,
                "native_handles_or_raw_ids_output": False,
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
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
