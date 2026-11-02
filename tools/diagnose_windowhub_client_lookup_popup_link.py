"""Read-only correlation of WindowHub Client LookupEdit and DataTable5 popup HWNDs.

The diagnostic locates the WindowHub-owned top-level form containing exactly
one UIA AutomationId match for IDC_ZAMAWIAJACY. It then compares that field's
native/UIA bounds and parent metadata with native DataTable5 descendants.

Only booleans, class names, count summaries, and coarse geometry relations
are emitted. No captions, UIA Name/Value/text, customer data, table headers
or cells, raw HWNDs, or native control IDs are emitted. No clicks, focus
changes, selections, pattern invocations, or mutations occur.
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
    _enumerate_child_hwnds,
    _enumerate_process_top_windows,
    _find_windowhub_root,
    _hwnd_value,
    _rect_nonempty,
)


LOOKUP_AUTOMATION_ID = "IDC_ZAMAWIAJACY"
FORM_CLASS_TOKEN = "idd_oferta_prop_view"
DATATABLE_CLASS_TOKEN = "datatable5"
MAX_PARENT_DEPTH = 8


def _configure_parent_api(api):
    api.GetParent.argtypes = (ctypes.wintypes.HWND,)
    api.GetParent.restype = ctypes.wintypes.HWND
    api.GetWindow.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.wintypes.UINT,
    )
    api.GetWindow.restype = ctypes.wintypes.HWND
    return api


def _normalize(value: object) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _read_win32_rect(api, hwnd: int):
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


def _read_uia_rect(wrapper):
    try:
        rect = wrapper.rectangle()
        left = int(rect.left)
        top = int(rect.top)
        right = int(rect.right)
        bottom = int(rect.bottom)
        if right <= left or bottom <= top:
            return None
        return (left, top, right, bottom)
    except Exception:
        return None


def _geometry_relation(field_rect, popup_rect) -> dict:
    if field_rect is None or popup_rect is None:
        return {
            "bounds_available": False,
            "horizontal_overlap": False,
            "popup_below_lookup": False,
            "vertical_gap_bucket": "unknown",
            "popup_width_relation": "unknown",
        }

    field_left, field_top, field_right, field_bottom = field_rect
    popup_left, popup_top, popup_right, popup_bottom = popup_rect

    horizontal_overlap = (
        min(field_right, popup_right) > max(field_left, popup_left)
    )
    if popup_top >= field_bottom:
        vertical_gap = popup_top - field_bottom
        popup_below = True
    elif field_top >= popup_bottom:
        vertical_gap = field_top - popup_bottom
        popup_below = False
    else:
        vertical_gap = 0
        popup_below = popup_top >= field_bottom

    if vertical_gap <= 20:
        gap_bucket = "0-20"
    elif vertical_gap <= 80:
        gap_bucket = "21-80"
    else:
        gap_bucket = "81+"

    popup_width = popup_right - popup_left
    field_width = field_right - field_left
    if popup_width > field_width * 1.2:
        width_relation = "wider_than_lookup"
    elif popup_width < field_width * 0.8:
        width_relation = "narrower_than_lookup"
    else:
        width_relation = "similar_to_lookup"

    return {
        "bounds_available": True,
        "horizontal_overlap": horizontal_overlap,
        "popup_below_lookup": popup_below,
        "vertical_gap_bucket": gap_bucket,
        "popup_width_relation": width_relation,
    }


def _native_parent_chain(api, hwnd: int) -> list[str]:
    chain = []
    current = hwnd
    seen = {hwnd}
    for _ in range(MAX_PARENT_DEPTH):
        parent = _hwnd_value(api.GetParent(current))
        if parent <= 0 or parent in seen:
            break
        seen.add(parent)
        chain.append(_class_name(api, parent))
        current = parent
    return chain


def _native_owner_chain(api, hwnd: int) -> list[int]:
    """Return private owner HWNDs; never serialize the values."""
    chain = []
    current = hwnd
    seen = {hwnd}
    for _ in range(MAX_PARENT_DEPTH):
        owner = _hwnd_value(api.GetWindow(current, 4))  # GW_OWNER
        if owner <= 0 or owner in seen:
            break
        seen.add(owner)
        chain.append(owner)
        current = owner
    return chain


def _native_owner_class_chain(api, hwnd: int) -> list[str]:
    return [
        _class_name(api, owner)
        for owner in _native_owner_chain(api, hwnd)
    ]


def _lookup_native_handle(lookup_wrapper) -> int:
    """Try pywinauto wrapper and UIA element-info HWND projections."""
    for candidate in (
        getattr(lookup_wrapper, "handle", None),
        getattr(
            getattr(lookup_wrapper, "element_info", None),
            "handle",
            None,
        ),
    ):
        try:
            handle = _hwnd_value(candidate)
        except (TypeError, ValueError):
            continue
        if handle > 0:
            return handle
    return 0


def _uia_descendants(wrapper):
    return tuple(wrapper.descendants())


def _find_form_and_lookup(desktop, api, enum_proc, root_hwnd, process_id):
    process_windows = _enumerate_process_top_windows(
        api,
        enum_proc,
        process_id,
    )
    matches = []

    for hwnd in process_windows:
        if _class_name(api, hwnd) != "#32770":
            continue
        root_owner = _hwnd_value(api.GetAncestor(hwnd, GA_ROOTOWNER))
        if root_owner != root_hwnd:
            continue
        try:
            form_wrapper = desktop.window(handle=hwnd).wrapper_object()
            descendants = _uia_descendants(form_wrapper)
        except Exception:
            continue

        lookup_controls = []
        form_marker_count = 0
        for item in descendants:
            try:
                info = item.element_info
                automation_id = _normalize(
                    getattr(info, "automation_id", None)
                )
                class_name = _normalize(
                    getattr(info, "class_name", None)
                )
                form_marker_count += int(
                    FORM_CLASS_TOKEN in class_name
                )
                if automation_id == LOOKUP_AUTOMATION_ID.casefold():
                    lookup_controls.append(item)
            except Exception:
                continue

        if len(lookup_controls) == 1:
            matches.append(
                {
                    "form_hwnd": hwnd,
                    "form_wrapper": form_wrapper,
                    "lookup_wrapper": lookup_controls[0],
                    "form_descendant_count": len(descendants),
                    "form_marker_count": form_marker_count,
                    "lookup_control_count": len(lookup_controls),
                }
            )

    if len(matches) != 1:
        raise RuntimeError(
            f"client_form_match_count_invalid:{len(matches)}"
        )
    return matches[0], len(process_windows)


def _inspect_datatable(api, desktop, form_hwnd, lookup_native_hwnd, lookup_rect, hwnd, root_hwnd):
    class_name = _class_name(api, hwnd)
    visible = bool(api.IsWindowVisible(hwnd))
    rect = _read_win32_rect(api, hwnd)

    try:
        wrapper = desktop.window(handle=hwnd).wrapper_object()
        descendants = _uia_descendants(wrapper)
        roles = Counter()
        for item in descendants:
            try:
                role = _normalize(
                    getattr(item.element_info, "control_type", None)
                )
                if role:
                    roles[role] += 1
            except Exception:
                continue
        uia_status = "ok"
        descendant_count = len(descendants)
        role_counts = dict(sorted(roles.items()))
    except Exception as exc:
        uia_status = f"failed:{type(exc).__name__}"
        descendant_count = 0
        role_counts = {}

    parent_chain = _native_parent_chain(api, hwnd)
    owner_handles = _native_owner_chain(api, hwnd)
    return {
        "native_class_name": class_name,
        "visible": visible,
        "nonempty_bounds": rect is not None,
        "native_parent_chain": parent_chain,
        "native_owner_class_chain": _native_owner_class_chain(api, hwnd),
        "parent_chain_contains_form": (
            form_hwnd in _native_parent_handles(api, hwnd)
        ),
        "owner_chain_contains_form": form_hwnd in owner_handles,
        "root_owner_is_windowhub": (
            _hwnd_value(api.GetAncestor(hwnd, GA_ROOTOWNER)) == root_hwnd
        ),
        "lookup_native_hwnd_available": lookup_native_hwnd > 0,
        "lookup_native_handle_matches_popup_parent": (
            lookup_native_hwnd > 0
            and lookup_native_hwnd in _native_parent_handles(api, hwnd)
        ),
        "lookup_native_handle_matches_popup_owner": (
            lookup_native_hwnd > 0
            and lookup_native_hwnd in owner_handles
        ),
        "geometry_to_client_lookup": _geometry_relation(
            lookup_rect,
            rect,
        ),
        "uia_scan_status": uia_status,
        "uia_descendant_count": descendant_count,
        "uia_control_type_counts": role_counts,
    }


def _native_parent_handles(api, hwnd: int) -> list[int]:
    handles = []
    current = hwnd
    seen = {hwnd}
    for _ in range(MAX_PARENT_DEPTH):
        parent = _hwnd_value(api.GetParent(current))
        if parent <= 0 or parent in seen:
            break
        seen.add(parent)
        handles.append(parent)
        current = parent
    return handles


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

        form, process_window_count = _find_form_and_lookup(
            desktop,
            api,
            enum_proc,
            root_hwnd,
            int(process_id.value),
        )

        lookup = form["lookup_wrapper"]
        lookup_rect = _read_uia_rect(lookup)
        lookup_native_hwnd = _lookup_native_handle(lookup)

        lookup_native_class = (
            _class_name(api, lookup_native_hwnd)
            if lookup_native_hwnd > 0
            else None
        )

        root_children = _enumerate_child_hwnds(
            api,
            enum_proc,
            root_hwnd,
        )
        form_children = _enumerate_child_hwnds(
            api,
            enum_proc,
            form["form_hwnd"],
        )

        datatable_handles = {
            hwnd
            for hwnd in root_children + form_children
            if DATATABLE_CLASS_TOKEN in _class_name(api, hwnd)
        }

        datatable_reports = [
            _inspect_datatable(
                api,
                desktop,
                form["form_hwnd"],
                lookup_native_hwnd,
                lookup_rect,
                hwnd,
                root_hwnd,
            )
            for hwnd in sorted(datatable_handles)
        ]

        datatable_reports.sort(
            key=lambda item: (
                not item["visible"],
                not item["owner_chain_contains_form"],
                not item["parent_chain_contains_form"],
                not item["lookup_native_handle_matches_popup_parent"],
                not item["lookup_native_handle_matches_popup_owner"],
                not item["geometry_to_client_lookup"]["horizontal_overlap"],
                not item["geometry_to_client_lookup"]["popup_below_lookup"],
            )
        )

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "windowhub_process_top_window_count": process_window_count,
            "form": {
                "matched_by_form_class_marker": (
                    form["form_marker_count"] >= 1
                ),
                "form_descendant_count": form["form_descendant_count"],
                "client_lookup_match_count": form["lookup_control_count"],
                "lookup_native_handle_available": (
                    lookup_native_hwnd > 0
                ),
                "lookup_native_class_name": lookup_native_class,
                "lookup_bounds_available": lookup_rect is not None,
                "lookup_native_parent_class_chain": (
                    _native_parent_chain(api, lookup_native_hwnd)
                    if lookup_native_hwnd > 0
                    else []
                ),
            },
            "datatable5_candidate_count": len(datatable_reports),
            "datatable5_candidates": datatable_reports[:20],
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
