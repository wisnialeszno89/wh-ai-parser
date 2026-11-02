"""Read-only UIA inspection of native WindowHub dialog subtrees.

The script starts from native #32770 HWNDs owned by WindowHub, then asks UIA
for structural metadata beneath each dialog. It never reads UIA Name/Value,
window captions beyond a fixed-prefix comparison, table headers/cells, or
customer data. It does not click, focus, invoke patterns, or change state.
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
    _configure_api,
    _enumerate_child_hwnds,
    _find_windowhub_root,
    _hwnd_value,
)
from tools.diagnose_windowhub_dialog_children import (
    _class_name,
    _configure_parent_api,
)


LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
GRID_AUTOMATION_ID = "PART_GridControl"
LOOKUP_CLASS_TOKEN = "lookupedit"
DATA_TABLE_CLASS_TOKEN = "datatable"


def _normalize(value: object) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _inspect_dialog_uia(desktop, hwnd: int, dialog_index: int) -> dict:
    result = {
        "dialog_index": dialog_index,
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
        # Use pywinauto's public Desktop.window(...).wrapper_object() path.
        # Avoid importing internal UIAWrapper/UIAElementInfo implementation
        # modules, whose import paths vary between pywinauto releases.
        dialog_spec = desktop.window(handle=hwnd)
        wrapper = dialog_spec.wrapper_object()
        descendants = tuple(wrapper.descendants())
    except Exception as exc:
        result["uia_scan_status"] = f"failed:{type(exc).__name__}"
        result["uia_error_type"] = type(exc).__name__
        return result

    control_types: Counter[str] = Counter()
    class_names: Counter[str] = Counter()
    structural_matches = []

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
            control_types[control_type] += 1
        if class_name:
            class_names[class_name] += 1

        is_lookup_id = automation_id == LOOKUP_AUTOMATION_ID.casefold()
        is_grid_id = automation_id == GRID_AUTOMATION_ID.casefold()
        is_lookup_class = LOOKUP_CLASS_TOKEN in class_name
        is_data_table_class = DATA_TABLE_CLASS_TOKEN in class_name
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
            structural_matches.append(
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
            "uia_error_type": None,
            "uia_descendant_count": len(descendants),
            "control_type_counts": dict(sorted(control_types.items())),
            "class_name_counts": dict(sorted(class_names.items())),
            "expected_lookup_automation_id_count": lookup_id_count,
            "expected_grid_automation_id_count": grid_id_count,
            "lookupedit_class_count": lookup_class_count,
            "data_table_class_count": data_table_class_count,
            "datagrid_control_type_count": datagrid_count,
            "table_control_type_count": table_count,
            "structural_matches": structural_matches[:40],
        }
    )
    return result


def _native_dialogs(api, enum_proc, root_hwnd: int):
    all_children = _enumerate_child_hwnds(api, enum_proc, root_hwnd)
    return [
        hwnd for hwnd in all_children
        if _class_name(api, hwnd) == "#32770"
    ]


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

        dialog_handles = _native_dialogs(
            api,
            enum_proc,
            root_hwnd,
        )
        reports = [
            _inspect_dialog_uia(desktop, hwnd, index)
            for index, hwnd in enumerate(dialog_handles, start=1)
        ]

        summary = {
            "result": "DIAGNOSTIC_ONLY",
            "native_dialog_count": len(dialog_handles),
            "uia_success_count": sum(
                item["uia_scan_status"] == "ok" for item in reports
            ),
            "dialogs": reports,
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
        print(json.dumps(summary, ensure_ascii=False, indent=2))
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
