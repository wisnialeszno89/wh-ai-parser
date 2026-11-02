"""Timed, read-only capture of a live WindowHub dropdown popup.

Run the script, then switch to WindowHub and open only the Client dropdown
while the script's observation window is active. Leave it open; do not select
a row. The script polls native HWND visibility for a bounded interval and
then captures structural UIA metadata for visible auxiliary windows.

No control/window captions, UIA Name/Value/text, customer values, table
headers/cells, raw handles, or native control IDs are emitted. It performs
no clicks, focus changes, pattern invocations, selections, or mutations.
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


OBSERVATION_SECONDS = 20.0
POLL_INTERVAL_SECONDS = 0.20
GW_OWNER = 4
POPUP_CLASS_TOKENS = (
    "combo",
    "list",
    "popup",
    "32768",
    "32770",
    "grid",
    "lookup",
    "dropdown",
    "datatable",
)


def _configure_owner_api(api):
    api.GetWindow.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.wintypes.UINT,
    )
    api.GetWindow.restype = ctypes.wintypes.HWND
    return api


def _owner_chain(api, hwnd: int, *, max_depth: int = 8) -> list[str]:
    classes: list[str] = []
    current = hwnd
    seen = {hwnd}
    for _ in range(max_depth):
        owner = _hwnd_value(api.GetWindow(current, GW_OWNER))
        if owner <= 0 or owner in seen:
            break
        seen.add(owner)
        classes.append(_class_name(api, owner))
        current = owner
    return classes


def _is_popup_class(class_name: str) -> bool:
    normalized = class_name.casefold()
    return any(token in normalized for token in POPUP_CLASS_TOKENS)


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
            "datagrid_control_type_count": 0,
            "table_control_type_count": 0,
            "datatable_class_count": 0,
        }

    roles: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    datagrid_count = 0
    table_count = 0
    datatable_count = 0
    lookup_id_count = 0
    grid_id_count = 0
    lookupedit_class_count = 0

    for item in descendants:
        try:
            info = item.element_info
            role = str(
                getattr(info, "control_type", "") or ""
            ).strip().casefold()
            class_name = str(
                getattr(info, "class_name", "") or ""
            ).strip().casefold()
        except Exception:
            continue

        if role:
            roles[role] += 1
        if class_name:
            classes[class_name] += 1
        datagrid_count += int(role == "datagrid")
        table_count += int(role == "table")
        datatable_count += int("datatable" in class_name)
        lookup_id_count += int(automation_id == "idc_zamawiajacy")
        grid_id_count += int(automation_id == "part_gridcontrol")
        lookupedit_class_count += int("lookupedit" in class_name)

    return {
        "uia_scan_status": "ok",
        "uia_descendant_count": len(descendants),
        "control_type_counts": dict(sorted(roles.items())),
        "class_name_counts": dict(sorted(classes.items())),
        "datagrid_control_type_count": datagrid_count,
        "table_control_type_count": table_count,
        "datatable_class_count": datatable_count,
        "expected_lookup_automation_id_count": lookup_id_count,
        "expected_grid_automation_id_count": grid_id_count,
        "lookupedit_class_count": lookupedit_class_count,
    }


def _candidate_record(api, hwnd: int, root_hwnd: int, source: str) -> dict:
    class_name = _class_name(api, hwnd)
    root_owner = _hwnd_value(api.GetAncestor(hwnd, GA_ROOTOWNER))
    visible = bool(api.IsWindowVisible(hwnd))
    return {
        "_hwnd": hwnd,
        "source": source,
        "native_class_name": class_name,
        "visible": visible,
        "nonempty_bounds": _rect_nonempty(api, hwnd),
        "root_owner_matches_windowhub": root_owner == root_hwnd,
        "owner_class_chain": _owner_chain(api, hwnd),
    }


def _capture_visible_candidates(
    api,
    enum_proc,
    root_hwnd: int,
    process_id: int,
) -> tuple[list[dict], dict]:
    candidates_by_handle: dict[int, dict] = {}

    native_children = _enumerate_child_hwnds(
        api,
        enum_proc,
        root_hwnd,
    )
    for hwnd in native_children:
        if hwnd == root_hwnd:
            continue
        if not bool(api.IsWindowVisible(hwnd)):
            continue
        class_name = _class_name(api, hwnd)
        if not _is_popup_class(class_name):
            continue
        candidates_by_handle[hwnd] = _candidate_record(
            api,
            hwnd,
            root_hwnd,
            "windowhub_native_child",
        )

    process_windows = _enumerate_process_top_windows(
        api,
        enum_proc,
        process_id,
    )
    for hwnd in process_windows:
        if hwnd == root_hwnd:
            continue
        if not bool(api.IsWindowVisible(hwnd)):
            continue
        class_name = _class_name(api, hwnd)
        record = _candidate_record(
            api,
            hwnd,
            root_hwnd,
            "same_process_top_level",
        )
        if (
            _is_popup_class(class_name)
            or record["root_owner_matches_windowhub"]
            or root_hwnd in _owner_handles(api, hwnd)
        ):
            previous = candidates_by_handle.get(hwnd)
            if previous is None:
                candidates_by_handle[hwnd] = record
            else:
                previous["source"] = "windowhub_native_child_and_top_level"

    records = list(candidates_by_handle.values())
    records.sort(
        key=lambda item: (
            not item["root_owner_matches_windowhub"],
            item["native_class_name"],
        )
    )
    visible_child_classes = Counter(
        _class_name(api, hwnd)
        for hwnd in native_children
        if bool(api.IsWindowVisible(hwnd))
    )
    return records, {
        "native_child_count": len(native_children),
        "process_top_level_count": len(process_windows),
        "visible_native_child_class_counts": dict(
            sorted(visible_child_classes.items())
        ),
    }


def _owner_handles(api, hwnd: int, *, max_depth: int = 8) -> list[int]:
    handles: list[int] = []
    current = hwnd
    seen = {hwnd}
    for _ in range(max_depth):
        owner = _hwnd_value(api.GetWindow(current, GW_OWNER))
        if owner <= 0 or owner in seen:
            break
        seen.add(owner)
        handles.append(owner)
        current = owner
    return handles


def main() -> int:
    if os.name != "nt":
        print(json.dumps({"result": "FAIL", "reason": "requires_windows"}))
        return 2

    try:
        sys.coinit_flags = 2
        from pywinauto import Desktop

        api, enum_proc = _configure_api()
        _configure_owner_api(api)
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

        print(
            "OBSERVACJA AKTYWNA przez 20 sekund. "
            "Przejdz teraz do WindowHub i otworz strzalke pola Klient. "
            "Nie wybieraj zadnego wiersza. Pozostaw liste otwarta; "
            "nie wracaj do terminala przed koncem odliczania.",
            flush=True,
        )

        deadline = time.monotonic() + OBSERVATION_SECONDS
        best_records: list[dict] = []
        best_counts: dict = {}
        best_score = (-1, -1)
        samples = 0

        while time.monotonic() < deadline:
            records, counts = _capture_visible_candidates(
                api,
                enum_proc,
                root_hwnd,
                int(process_id.value),
            )
            samples += 1

            # Keep the richest snapshot observed during the interval. This
            # preserves a popup even if it closes before the timer expires.
            specificity = sum(
                _is_popup_class(item["native_class_name"])
                for item in records
            )
            score = (len(records), specificity)
            if records and score > best_score:
                best_records = records
                best_counts = counts
                best_score = score

            time.sleep(POLL_INTERVAL_SECONDS)

        reports = []
        for item in best_records:
            report = {
                key: value
                for key, value in item.items()
                if not key.startswith("_")
            }
            report.update(
                _inspect_uia_subtree(
                    desktop,
                    item["_hwnd"],
                )
            )
            reports.append(report)

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "observation_window_seconds": OBSERVATION_SECONDS,
            "poll_samples": samples,
            "captured_visible_candidate_count": len(reports),
            "native_inventory_at_capture": best_counts,
            "visible_candidates": reports[:40],
            "capture_note": (
                "No eligible visible auxiliary window was observed. "
                "The dropdown may not have been opened during the capture "
                "window, or the popup may not expose a separate visible HWND."
                if not reports
                else "Captured the last/best visible auxiliary-window snapshot."
            ),
            "privacy": {
                "window_caption_compared_to_fixed_prefix_only": True,
                "window_captions_output": False,
                "uia_name_or_value_or_text_read": False,
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
