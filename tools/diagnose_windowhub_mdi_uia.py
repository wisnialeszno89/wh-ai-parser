"""Read-only UIA inventory of WindowHub MDI child windows.

Native Win32 enumeration identifies direct children of the MDI client. Each
candidate is then used as a UIA root so the scan is not limited to the main
frame or #32770 dialogs. Only structural metadata is emitted: control types,
class names, AutomationId match booleans, visibility and enabled state.

No UIA Name/Value/text, customer data, table headers/cells, raw HWND values,
clicks, focus changes, or pattern invocations are used.
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
    _class_name,
    _configure_api,
    _enumerate_child_hwnds,
    _find_windowhub_root,
    _hwnd_value,
)


LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
GRID_AUTOMATION_ID = "PART_GridControl"


def _configure_parent_api(api):
    api.GetParent.argtypes = (ctypes.wintypes.HWND,)
    api.GetParent.restype = ctypes.wintypes.HWND
    return api


def _direct_parent_class(api, hwnd: int) -> str:
    parent = _hwnd_value(api.GetParent(hwnd))
    if parent <= 0:
        return ""
    return _class_name(api, parent)


def _find_mdi_child_roots(api, hwnds: list[int]) -> list[tuple[int, str]]:
    """Return native descendants whose immediate parent is an MDI client."""
    candidates: list[tuple[int, str]] = []
    for hwnd in hwnds:
        if _direct_parent_class(api, hwnd) != "mdiclient":
            continue
        class_name = _class_name(api, hwnd)
        candidates.append((hwnd, class_name))
    return candidates


def _normalize(value: object) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _inspect_mdi_child_uia(desktop, hwnd: int, index: int, native_class: str) -> dict:
    result = {
        "mdi_child_index": index,
        "native_class_name": native_class,
        "uia_scan_status": "not_started",
        "uia_error_type": None,
        "uia_descendant_count": 0,
        "control_type_counts": {},
        "class_name_counts": {},
        "expected_lookup_automation_id_count": 0,
        "expected_grid_automation_id_count": 0,
        "lookupedit_class_count": 0,
        "data_table_class_count": 0,
        "datagrid_control_type_count": 0,
        "table_control_type_count": 0,
        "structural_matches": [],
    }
    try:
        wrapper = desktop.window(handle=hwnd).wrapper_object()
        descendants = tuple(wrapper.descendants())
    except Exception as exc:
        result["uia_scan_status"] = f"failed:{type(exc).__name__}"
        result["uia_error_type"] = type(exc).__name__
        return result

    roles: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    matches: list[dict] = []
    lookup_id_count = 0
    grid_id_count = 0
    lookup_class_count = 0
    data_table_class_count = 0
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
            visible = bool(getattr(info, "visible", True))
            enabled = bool(getattr(info, "enabled", False))
        except Exception:
            continue

        if control_type:
            roles[control_type] += 1
        if class_name:
            classes[class_name] += 1

        is_lookup_id = automation_id == LOOKUP_AUTOMATION_ID.casefold()
        is_grid_id = automation_id == GRID_AUTOMATION_ID.casefold()
        is_lookup_class = "lookupedit" in class_name
        is_data_table_class = "datatable" in class_name
        is_datagrid = control_type == "datagrid"
        is_table = control_type == "table"

        lookup_id_count += int(is_lookup_id)
        grid_id_count += int(is_grid_id)
        lookup_class_count += int(is_lookup_class)
        data_table_class_count += int(is_data_table_class)
        datagrid_count += int(is_datagrid)
        table_count += int(is_table)

        if (
            is_lookup_id
            or is_grid_id
            or is_lookup_class
            or is_data_table_class
            or is_datagrid
            or is_table
        ):
            matches.append(
                {
                    "control_type": control_type or None,
                    "class_name": class_name or None,
                    "expected_lookup_id_match": is_lookup_id,
                    "expected_grid_id_match": is_grid_id,
                    "lookupedit_class_match": is_lookup_class,
                    "datatable_class_match": is_data_table_class,
                    "visible": visible,
                    "enabled": enabled,
                }
            )

    result.update(
        {
            "uia_scan_status": "ok",
            "uia_descendant_count": len(descendants),
            "control_type_counts": dict(sorted(roles.items())),
            "class_name_counts": dict(sorted(classes.items())),
            "expected_lookup_automation_id_count": lookup_id_count,
            "expected_grid_automation_id_count": grid_id_count,
            "lookupedit_class_count": lookup_class_count,
            "data_table_class_count": data_table_class_count,
            "datagrid_control_type_count": datagrid_count,
            "table_control_type_count": table_count,
            "structural_matches": matches[:60],
        }
    )
    return result


def main() -> int:
    if os.name != "nt":
        print(json.dumps({"result": "FAIL", "reason": "requires_windows"}))
        return 2

    try:
        sys.coinit_flags = 2
        from pywinauto import Desktop

        api, enum_proc = _configure_api()
        _configure_parent_api(api)

        desktop = Desktop(backend="uia")
        root = _find_windowhub_root(desktop)
        root_hwnd = _hwnd_value(root.handle)
        if root_hwnd <= 0:
            raise RuntimeError("windowhub_root_handle_invalid")

        descendants = _enumerate_child_hwnds(api, enum_proc, root_hwnd)
        mdi_children = _find_mdi_child_roots(api, descendants)

        reports = [
            _inspect_mdi_child_uia(
                desktop,
                hwnd,
                index,
                class_name,
            )
            for index, (hwnd, class_name) in enumerate(
                mdi_children,
                start=1,
            )
        ]

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "native_descendant_count": len(descendants),
            "native_mdi_child_count": len(mdi_children),
            "uia_success_count": sum(
                report["uia_scan_status"] == "ok"
                for report in reports
            ),
            "mdi_children": reports,
            "privacy": {
                "window_caption_compared_to_fixed_prefix_only": True,
                "window_caption_output": False,
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
