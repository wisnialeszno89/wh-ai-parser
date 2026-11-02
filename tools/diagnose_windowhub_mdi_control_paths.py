"""Read-only semantic paths for structural controls in WindowHub MDI children.

This diagnostic follows the native MDI child roots already established by
Win32 enumeration and reports only UIA class names, control types, visibility,
enabled state, and boolean matches for known AutomationIds/classes.

It never reads Name, Value, text, table headers/cells, or customer data. It
never clicks, focuses, invokes patterns, or changes application state.
"""
from __future__ import annotations

import ctypes.wintypes
import json
import os
import sys
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
from tools.diagnose_windowhub_mdi_uia import (
    _configure_parent_api,
    _find_mdi_child_roots,
)


LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
GRID_AUTOMATION_ID = "PART_GridControl"
CANDIDATE_CONTROL_TYPES = frozenset(
    {
        "button",
        "combobox",
        "edit",
        "datagrid",
        "table",
        "custom",
        "pane",
        "document",
    }
)


def _normalize(value: object) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _safe_element_metadata(item) -> dict:
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
    return {
        "control_type": control_type or None,
        "class_name": class_name or None,
        "visible": bool(getattr(info, "visible", True)),
        "enabled": bool(getattr(info, "enabled", False)),
        "matches_lookup_automation_id": (
            automation_id == LOOKUP_AUTOMATION_ID.casefold()
        ),
        "matches_grid_automation_id": (
            automation_id == GRID_AUTOMATION_ID.casefold()
        ),
        "matches_lookupedit_class": "lookupedit" in class_name,
        "matches_datatable_class": "datatable" in class_name,
    }


def _parent_metadata_chain(item, *, max_depth: int = 6) -> list[dict]:
    chain: list[dict] = []
    current = item
    for _ in range(max_depth):
        parent_getter = getattr(current, "parent", None)
        if not callable(parent_getter):
            break
        try:
            current = parent_getter()
            if current is None:
                break
            info = current.element_info
            control_type = _normalize(
                getattr(info, "control_type", None)
            )
            class_name = _normalize(
                getattr(info, "class_name", None)
            )
            automation_id = _normalize(
                getattr(info, "automation_id", None)
            )
            chain.append(
                {
                    "control_type": control_type or None,
                    "class_name": class_name or None,
                    "matches_lookup_automation_id": (
                        automation_id == LOOKUP_AUTOMATION_ID.casefold()
                    ),
                    "matches_grid_automation_id": (
                        automation_id == GRID_AUTOMATION_ID.casefold()
                    ),
                }
            )
        except Exception:
            break
    return chain


def _is_candidate(metadata: dict) -> bool:
    return (
        metadata.get("control_type") in CANDIDATE_CONTROL_TYPES
        or metadata.get("matches_lookup_automation_id", False)
        or metadata.get("matches_grid_automation_id", False)
        or metadata.get("matches_lookupedit_class", False)
        or metadata.get("matches_datatable_class", False)
    )


def _inspect_mdi_child(desktop, hwnd: int, index: int, native_class: str) -> dict:
    try:
        wrapper = desktop.window(handle=hwnd).wrapper_object()
        descendants = tuple(wrapper.descendants())
    except Exception as exc:
        return {
            "mdi_child_index": index,
            "native_class_name": native_class,
            "uia_scan_status": f"failed:{type(exc).__name__}",
            "uia_descendant_count": 0,
            "candidate_count": 0,
            "candidate_controls": [],
        }

    candidates: list[dict] = []
    role_counts: dict[str, int] = {}
    lookup_id_count = 0
    grid_id_count = 0
    lookup_class_count = 0
    datatable_class_count = 0
    datagrid_count = 0

    for item in descendants:
        try:
            metadata = _safe_element_metadata(item)
        except Exception:
            continue

        role = metadata["control_type"]
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1

        lookup_id_count += int(metadata["matches_lookup_automation_id"])
        grid_id_count += int(metadata["matches_grid_automation_id"])
        lookup_class_count += int(metadata["matches_lookupedit_class"])
        datatable_class_count += int(metadata["matches_datatable_class"])
        datagrid_count += int(role == "datagrid")

        if _is_candidate(metadata):
            candidates.append(
                {
                    **metadata,
                    "ancestor_chain": _parent_metadata_chain(item),
                }
            )

    return {
        "mdi_child_index": index,
        "native_class_name": native_class,
        "uia_scan_status": "ok",
        "uia_descendant_count": len(descendants),
        "control_type_counts": dict(sorted(role_counts.items())),
        "expected_lookup_automation_id_count": lookup_id_count,
        "expected_grid_automation_id_count": grid_id_count,
        "lookupedit_class_count": lookup_class_count,
        "datatable_class_count": datatable_class_count,
        "datagrid_control_type_count": datagrid_count,
        "candidate_count": len(candidates),
        "candidate_controls": candidates[:80],
    }


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

        native_descendants = _enumerate_child_hwnds(
            api,
            enum_proc,
            root_hwnd,
        )
        mdi_children = _find_mdi_child_roots(
            api,
            native_descendants,
        )

        reports = [
            _inspect_mdi_child(
                desktop,
                hwnd,
                index,
                native_class,
            )
            for index, (hwnd, native_class) in enumerate(
                mdi_children,
                start=1,
            )
        ]

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "native_mdi_child_count": len(mdi_children),
            "uia_success_count": sum(
                item["uia_scan_status"] == "ok" for item in reports
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
