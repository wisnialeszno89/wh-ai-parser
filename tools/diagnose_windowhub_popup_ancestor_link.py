"""Read-only ancestor correlation for WindowHub Client LookupEdit/DataTable5.

Finds the unique WindowHub-owned form containing IDC_ZAMAWIAJACY, walks the
UIA ancestor chain of that LookupEdit, and inspects native #32770 ancestors
of visible DataTable5 controls. This tests whether a WPF/DevExpress lookup
has no HWND of its own but belongs to an HWND-backed parent, and whether a
table popup is hosted by a dialog containing the lookup.

Only structural metadata, boolean handle matches, and coarse spatial
relations are output. No control captions, UIA Name/Value/text, customer
data, table headers/cells, raw HWNDs, or native control IDs are exposed.
No clicks, focus changes, pattern invocations, selections, or mutations.
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

from tools.diagnose_windowhub_client_lookup_popup_link import (
    DATATABLE_CLASS_TOKEN,
    FORM_CLASS_TOKEN,
    LOOKUP_AUTOMATION_ID,
    MAX_PARENT_DEPTH,
    _configure_parent_api,
    _find_form_and_lookup,
    _native_owner_chain,
    _native_parent_handles,
    _read_uia_rect,
    _geometry_relation,
)
from tools.diagnose_windowhub_win32_children import (
    GA_ROOTOWNER,
    _class_name,
    _configure_api,
    _enumerate_child_hwnds,
    _enumerate_process_top_windows,
    _find_windowhub_root,
    _hwnd_value,
    _read_win32_rect if False else _rect_nonempty,
)


def _native_rect(api, hwnd: int):
    rect = ctypes.wintypes.RECT()
    if not api.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    if rect.right <= rect.left or rect.bottom <= rect.top:
        return None
    return (
        int(rect.left),
        int(rect.top),
        int(rect.right),
        int(rect.bottom),
    )


def _safe_info(item) -> dict:
    info = item.element_info
    return {
        "control_type": str(
            getattr(info, "control_type", "") or ""
        ).strip().casefold() or None,
        "class_name": str(
            getattr(info, "class_name", "") or ""
        ).strip().casefold() or None,
        "matches_lookup_automation_id": (
            str(getattr(info, "automation_id", "") or "")
            .strip()
            .casefold()
            == LOOKUP_AUTOMATION_ID.casefold()
        ),
    }


def _element_hwnd(item) -> int:
    info = getattr(item, "element_info", None)
    try:
        raw = getattr(info, "handle", None)
        return _hwnd_value(raw)
    except Exception:
        return 0


def _uia_ancestor_path(item, form_hwnd: int) -> list[dict]:
    chain: list[dict] = []
    current = item
    seen_handles: set[int] = set()

    for _ in range(MAX_PARENT_DEPTH):
        getter = getattr(current, "parent", None)
        if not callable(getter):
            break
        try:
            parent = getter()
            if parent is None:
                break
            metadata = _safe_info(parent)
            hwnd = _element_hwnd(parent)
            if hwnd > 0:
                seen_handles.add(hwnd)
            chain.append(
                {
                    **metadata,
                    "native_hwnd_available": hwnd > 0,
                    "native_hwnd_matches_form": (
                        hwnd > 0 and hwnd == form_hwnd
                    ),
                }
            )
            current = parent
        except Exception:
            break

    return chain


def _inspect_dialog_ancestor(api, desktop, hwnd: int, form_hwnd: int) -> dict:
    try:
        wrapper = desktop.window(handle=hwnd).wrapper_object()
        descendants = tuple(wrapper.descendants())
        roles = Counter()
        classes = Counter()
        lookup_matches = 0
        form_markers = 0
        datatable_matches = 0

        for item in descendants:
            try:
                info = item.element_info
                role = str(
                    getattr(info, "control_type", "") or ""
                ).strip().casefold()
                class_name = str(
                    getattr(info, "class_name", "") or ""
                ).strip().casefold()
                automation_id = str(
                    getattr(info, "automation_id", "") or ""
                ).strip().casefold()
            except Exception:
                continue

            if role:
                roles[role] += 1
            if class_name:
                classes[class_name] += 1
            lookup_matches += int(
                automation_id == LOOKUP_AUTOMATION_ID.casefold()
            )
            form_markers += int(FORM_CLASS_TOKEN in class_name)
            datatable_matches += int(
                DATATABLE_CLASS_TOKEN in class_name
            )

        return {
            "uia_scan_status": "ok",
            "uia_descendant_count": len(descendants),
            "lookup_automation_id_count": lookup_matches,
            "form_class_marker_count": form_markers,
            "datatable_class_count": datatable_matches,
            "control_type_counts": dict(sorted(roles.items())),
            "class_name_counts": dict(sorted(classes.items())),
        }
    except Exception as exc:
        return {
            "uia_scan_status": f"failed:{type(exc).__name__}",
            "uia_descendant_count": 0,
            "lookup_automation_id_count": 0,
            "form_class_marker_count": 0,
            "datatable_class_count": 0,
            "control_type_counts": {},
            "class_name_counts": {},
        }


def _inspect_table_ancestors(
    api,
    desktop,
    table_hwnd: int,
    form_hwnd: int,
    lookup_rect,
) -> dict:
    parent_handles = _native_parent_handles(api, table_hwnd)
    owner_handles = _native_owner_chain(api, table_hwnd)
    ancestor_handles = list(dict.fromkeys(parent_handles + owner_handles))

    dialog_ancestors = []
    for ancestor in ancestor_handles:
        if _class_name(api, ancestor) != "#32770":
            continue
        dialog_ancestors.append(
            {
                "native_class_name": "#32770",
                "is_form_hwnd": ancestor == form_hwnd,
                "visible": bool(api.IsWindowVisible(ancestor)),
                "nonempty_bounds": _rect_nonempty(api, ancestor),
                **_inspect_dialog_ancestor(
                    api,
                    desktop,
                    ancestor,
                    form_hwnd,
                ),
            }
        )

    return {
        "native_parent_class_chain": [
            _class_name(api, handle)
            for handle in parent_handles
        ],
        "native_owner_class_chain": [
            _class_name(api, handle)
            for handle in owner_handles
        ],
        "parent_chain_contains_form": form_hwnd in parent_handles,
        "owner_chain_contains_form": form_hwnd in owner_handles,
        "dialog_ancestors": dialog_ancestors,
        "geometry_to_client_lookup": _geometry_relation(
            lookup_rect,
            _native_rect(api, table_hwnd),
        ),
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

        process_id = ctypes.wintypes.DWORD()
        api.GetWindowThreadProcessId(
            root_hwnd,
            ctypes.byref(process_id),
        )
        if process_id.value == 0:
            raise RuntimeError("windowhub_process_id_unavailable")

        form, process_count = _find_form_and_lookup(
            desktop,
            api,
            enum_proc,
            root_hwnd,
            int(process_id.value),
        )
        lookup = form["lookup_wrapper"]
        lookup_rect = _read_uia_rect(lookup)
        lookup_ancestor_path = _uia_ancestor_path(
            lookup,
            form["form_hwnd"],
        )

        lookup_handle_chain = [
            item for item in lookup_ancestor_path
            if item["native_hwnd_available"]
        ]

        native_descendants = _enumerate_child_hwnds(
            api,
            enum_proc,
            root_hwnd,
        )
        table_handles = sorted(
            {
                hwnd for hwnd in native_descendants
                if DATATABLE_CLASS_TOKEN in _class_name(api, hwnd)
                and bool(api.IsWindowVisible(hwnd))
            }
        )

        tables = [
            {
                "table_index": index,
                "native_class_name": DATATABLE_CLASS_TOKEN,
                "visible": True,
                **_inspect_table_ancestors(
                    api,
                    desktop,
                    hwnd,
                    form["form_hwnd"],
                    lookup_rect,
                ),
            }
            for index, hwnd in enumerate(table_handles, start=1)
        ]

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "windowhub_process_top_window_count": process_count,
            "form": {
                "form_descendant_count": form["form_descendant_count"],
                "client_lookup_match_count": form["lookup_control_count"],
                "lookup_native_hwnd_available": (
                    _element_hwnd(lookup) > 0
                ),
                "lookup_native_hwnd_parent_path": lookup_handle_chain,
                "lookup_uia_ancestor_path": lookup_ancestor_path,
            },
            "visible_datatable5_count": len(tables),
            "visible_datatable5": tables,
            "privacy": {
                "window_captions_output": False,
                "uia_name_or_value_or_text_read": False,
                "customer_text_or_values_read": False,
                "table_headers_or_cells_read": False,
                "coordinates_or_raw_handles_output": False,
                "native_control_ids_output": False,
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
