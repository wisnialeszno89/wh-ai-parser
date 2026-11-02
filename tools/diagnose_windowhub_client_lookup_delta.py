"""Read-only before/after structural diff for the WindowHub Client dropdown.

Start with the Client dropdown CLOSED. The script captures a baseline, then
asks the user to open the dropdown and leave it open. It compares native
window lifecycle/visibility/bounds and UIA structure under the known offer
form. It never reads window captions except the fixed WindowHub root prefix,
UIA Name/Value/text, customer data, table headers/cells, or raw HWND values.

No clicks, focus changes, UIA pattern invocations, record selections, or
offer mutations are performed.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.diagnose_windowhub_client_lookup_popup_link import (
    DATATABLE_CLASS_TOKEN,
    FORM_CLASS_TOKEN,
    LOOKUP_AUTOMATION_ID,
    _configure_parent_api,
    _find_form_and_lookup,
    _native_owner_chain,
    _native_parent_handles,
)
from tools.diagnose_windowhub_win32_children import (
    GA_ROOTOWNER,
    _class_name,
    _configure_api,
    _enumerate_child_hwnds,
    _enumerate_process_top_windows,
    _find_windowhub_root,
    _hwnd_value,
)

OBSERVATION_SECONDS = 15.0
POLL_INTERVAL_SECONDS = 0.30
GRID_AUTOMATION_ID = "part_gridcontrol"
CONTENT_ROLES = {
    "cell",
    "dataitem",
    "header",
    "headeritem",
    "image",
    "listitem",
    "row",
    "text",
    "treeitem",
}


def _native_rect(api, hwnd: int):
    rect = ctypes.wintypes.RECT()
    try:
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
    except Exception:
        return None


def _native_window_snapshot(
    api,
    enum_proc,
    root_hwnd: int,
    process_id: int,
) -> dict[int, dict]:
    """Capture private HWND-keyed structure; never serialize HWND keys."""
    handles = set(
        _enumerate_child_hwnds(api, enum_proc, root_hwnd)
    )
    process_windows = _enumerate_process_top_windows(
        api,
        enum_proc,
        process_id,
    )
    for hwnd in process_windows:
        if _hwnd_value(api.GetAncestor(hwnd, GA_ROOTOWNER)) == root_hwnd:
            handles.add(hwnd)

    snapshot = {}
    for hwnd in handles:
        if hwnd == root_hwnd:
            continue
        snapshot[hwnd] = {
            "class_name": _class_name(api, hwnd),
            "visible": bool(api.IsWindowVisible(hwnd)),
            "rect": _native_rect(api, hwnd),
            "parent_class_chain": [
                _class_name(api, parent)
                for parent in _native_parent_handles(api, hwnd)
            ],
            "owner_class_chain": [
                _class_name(api, owner)
                for owner in _native_owner_chain(api, hwnd)
            ],
        }
    return snapshot


def _diff_window_snapshots(
    before: dict[int, dict],
    after: dict[int, dict],
) -> list[dict]:
    """Return changed records with private HWNDs for internal later lookup."""
    changes = []
    for hwnd, current in after.items():
        previous = before.get(hwnd)
        kinds = []
        if previous is None:
            kinds.append("new_window")
        else:
            if current["visible"] and not previous["visible"]:
                kinds.append("became_visible")
            if current["rect"] != previous["rect"]:
                kinds.append("bounds_changed")
            if current["class_name"] != previous["class_name"]:
                kinds.append("class_changed")
        if kinds:
            changes.append(
                {
                    "_hwnd": hwnd,
                    "class_name": current["class_name"],
                    "visible": current["visible"],
                    "has_bounds": current["rect"] is not None,
                    "parent_class_chain": current["parent_class_chain"],
                    "owner_class_chain": current["owner_class_chain"],
                    "change_kinds": kinds,
                }
            )
    changes.sort(
        key=lambda item: (
            "new_window" not in item["change_kinds"],
            "became_visible" not in item["change_kinds"],
            item["class_name"],
        )
    )
    return changes


def _uia_structure_snapshot(wrapper) -> dict:
    """Count structural UIA metadata only; omit content-bearing element roles."""
    descendants = tuple(wrapper.descendants())
    pairs = Counter()
    lookup_id_count = 0
    grid_id_count = 0
    form_class_count = 0
    datatable_class_count = 0

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
            visible = bool(getattr(info, "visible", True))
        except Exception:
            continue

        lookup_id_count += int(
            automation_id == LOOKUP_AUTOMATION_ID.casefold()
        )
        grid_id_count += int(automation_id == GRID_AUTOMATION_ID)
        form_class_count += int(FORM_CLASS_TOKEN in class_name)
        datatable_class_count += int(
            DATATABLE_CLASS_TOKEN in class_name
        )

        if role in CONTENT_ROLES:
            continue
        pairs[(role or "<unknown>", class_name or "<unknown>", visible)] += 1

    return {
        "descendant_count": len(descendants),
        "structural_counts": pairs,
        "lookup_automation_id_count": lookup_id_count,
        "grid_automation_id_count": grid_id_count,
        "form_class_marker_count": form_class_count,
        "datatable_class_count": datatable_class_count,
    }


def _structure_delta(before: dict, after: dict) -> dict:
    old_counts = before["structural_counts"]
    new_counts = after["structural_counts"]
    added = new_counts - old_counts
    removed = old_counts - new_counts

    def pack(counter):
        rows = [
            {
                "control_type": role,
                "class_name": class_name,
                "visible": visible,
                "count": count,
            }
            for (role, class_name, visible), count in counter.items()
        ]
        rows.sort(
            key=lambda item: (
                item["control_type"],
                item["class_name"],
                item["visible"],
            )
        )
        return rows[:40]

    return {
        "descendant_count_before": before["descendant_count"],
        "descendant_count_after": after["descendant_count"],
        "added_structural_elements": pack(added),
        "removed_structural_elements": pack(removed),
        "lookup_automation_id_count_before": (
            before["lookup_automation_id_count"]
        ),
        "lookup_automation_id_count_after": (
            after["lookup_automation_id_count"]
        ),
        "grid_automation_id_count_before": (
            before["grid_automation_id_count"]
        ),
        "grid_automation_id_count_after": (
            after["grid_automation_id_count"]
        ),
        "datatable_class_count_before": (
            before["datatable_class_count"]
        ),
        "datatable_class_count_after": (
            after["datatable_class_count"]
        ),
    }


def _inspect_changed_window(desktop, record: dict) -> dict:
    result = {
        key: value
        for key, value in record.items()
        if not key.startswith("_")
    }
    try:
        wrapper = desktop.window(
            handle=record["_hwnd"]
        ).wrapper_object()
        descendants = tuple(wrapper.descendants())
        roles = Counter()
        classes = Counter()
        lookup_count = 0
        grid_count = 0
        datatable_count = 0

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

            if role and role not in CONTENT_ROLES:
                roles[role] += 1
            if class_name:
                classes[class_name] += 1
            lookup_count += int(
                automation_id == LOOKUP_AUTOMATION_ID.casefold()
            )
            grid_count += int(automation_id == GRID_AUTOMATION_ID)
            datatable_count += int(
                DATATABLE_CLASS_TOKEN in class_name
            )

        result.update(
            {
                "uia_scan_status": "ok",
                "uia_descendant_count": len(descendants),
                "structural_control_type_counts": dict(sorted(roles.items())),
                "class_name_counts": dict(sorted(classes.items())) ,
                "lookup_automation_id_count": lookup_count,
                "grid_automation_id_count": grid_count,
                "datatable_class_count": datatable_count,
            }
        )
    except Exception as exc:
        result.update(
            {
                "uia_scan_status": f"failed:{type(exc).__name__}",
                "uia_descendant_count": 0,
                "structural_control_type_counts": {},
                "class_name_counts": {},
                "lookup_automation_id_count": 0,
                "grid_automation_id_count": 0,
                "datatable_class_count": 0,
            }
        )
    return result


def _score(changes: list[dict], delta: dict) -> int:
    return (
        len(changes) * 10
        + len(delta["added_structural_elements"]) * 3
        + len(delta["removed_structural_elements"])
        + abs(
            delta["descendant_count_after"]
            - delta["descendant_count_before"]
        )
    )


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
        form_wrapper = form["form_wrapper"]

        print(
            "PRZYGOTOWANIE: pozostaw formularz nowej oferty otwarty, "
            "a liste Klient ZAMKNIETA. Zbieram stan bazowy...",
            flush=True,
        )
        baseline_windows = _native_window_snapshot(
            api,
            enum_proc,
            root_hwnd,
            int(process_id.value),
        )
        baseline_uia = _uia_structure_snapshot(form_wrapper)

        print(
            "TERAZ przez 15 sekund otworz strzalke pola Klient "
            "i pozostaw liste otwarta. Nie wybieraj zadnego rekordu.",
            flush=True,
        )

        deadline = time.monotonic() + OBSERVATION_SECONDS
        best = None
        best_score = -1
        samples = 0

        while time.monotonic() < deadline:
            current_windows = _native_window_snapshot(
                api,
                enum_proc,
                root_hwnd,
                int(process_id.value),
            )
            current_uia = _uia_structure_snapshot(form_wrapper)
            changes = _diff_window_snapshots(
                baseline_windows,
                current_windows,
            )
            delta = _structure_delta(baseline_uia, current_uia)
            score = _score(changes, delta)
            samples += 1

            if score > best_score:
                best_score = score
                best = {
                    "changes": changes,
                    "delta": delta,
                }
            time.sleep(POLL_INTERVAL_SECONDS)

        if best is None:
            best = {
                "changes": [],
                "delta": _structure_delta(
                    baseline_uia,
                    baseline_uia,
                ),
            }

        changed_windows = [
            _inspect_changed_window(desktop, record)
            for record in best["changes"][:30]
        ]

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "windowhub_process_top_window_count": process_count,
            "observation_seconds": OBSERVATION_SECONDS,
            "poll_samples": samples,
            "baseline_native_window_count": len(baseline_windows),
            "changed_native_window_count": len(best["changes"]),
            "changed_native_windows": changed_windows,
            "form_uia_delta": best["delta"],
            "privacy": {
                "window_captions_compared_to_fixed_prefix_only": True,
                "window_captions_output": False,
                "uia_name_value_or_text_read": False,
                "customer_text_or_values_read": False,
                "table_headers_or_cells_read": False,
                "content_bearing_uia_roles_aggregated": False,
                "raw_hwnds_or_native_ids_output": False,
                "coordinates_output": False,
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
