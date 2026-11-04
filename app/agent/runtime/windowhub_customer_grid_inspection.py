"""Observe a WindowHub-owned customer lookup grid beyond the foreground dialog.

The popup can live in a separate native HWND, so generic foreground-only UIA
does not necessarily include it. This reader does not execute interactions.
It emits bounded structural evidence plus blank-name candidate indices, never
customer names or other business record values.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import os


@dataclass(frozen=True)
class CustomerLookupGridObservation:
    status: str
    grid_count: int = 0
    reported_rows: int | None = None
    reported_columns: int | None = None
    inspected_rows: int = 0
    header_labels: tuple[str, ...] = ()
    blank_name_candidate_indices: tuple[int, ...] = ()
    reason: str = ""


def _ui_text(element):
    """Read only one UIA cell or header via Value/Name, without OCR."""
    for attr in ("CurrentName", "CurrentValue"):
        try:
            value = getattr(element, attr, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        except Exception:
            pass
    info = getattr(element, "element_info", None)
    if info is not None:
        for attr in ("name", "value"):
            try:
                value = getattr(info, attr, None)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            except Exception:
                pass
    for attr in ("window_text", "get_value"):
        try:
            method = getattr(element, attr, None)
            value = method() if callable(method) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
        except Exception:
            pass
    return ""


def _rows_from_grid(grid, *, max_rows=12):
    pattern = getattr(grid, "iface_grid", None)
    if pattern is None:
        return CustomerLookupGridObservation("grid_pattern_missing")
    try:
        row_count = int(pattern.CurrentRowCount)
        column_count = int(pattern.CurrentColumnCount)
    except Exception:
        return CustomerLookupGridObservation("grid_counts_unavailable")
    if not (0 <= row_count <= 100000 and 1 <= column_count <= 64):
        return CustomerLookupGridObservation("grid_counts_invalid")

    headers = ()
    try:
        table = getattr(grid, "iface_table", None)
        if table is not None:
            raw = table.GetCurrentColumnHeaders()
            headers = tuple(_ui_text(h)[:80] for h in list(raw)[:column_count])
    except Exception:
        headers = ()

    # A blank value in the *name column* is not by itself proof of an
    # intentionally blank customer. We report candidates, never select them.
    name_indices = [
        i for i, label in enumerate(headers)
        if any(token in label.casefold() for token in (
            "nazwa", "name", "klient", "firma", "imię", "imie"
        ))
    ]
    candidates = []
    fully_blank = []
    inspected = min(row_count, max_rows)
    for row in range(inspected):
        try:
            values = [_ui_text(pattern.GetItem(row, col)) for col in range(column_count)]
        except Exception:
            continue
        if all(not value.strip() for value in values):
            fully_blank.append(row)
        if len(name_indices) == 1 and not values[name_indices[0]].strip():
            candidates.append(row)

    return CustomerLookupGridObservation(
        "grid_read",
        grid_count=1,
        reported_rows=row_count,
        reported_columns=column_count,
        inspected_rows=inspected,
        header_labels=headers,
        blank_name_candidate_indices=tuple(candidates),
        fully_blank_candidate_indices=tuple(fully_blank),
        reason=(
            "All-empty rows and unnamed rows are observational candidates only; no selection authorized."
        ),
    )


def inspect_live_customer_grid(*, max_rows=12) -> CustomerLookupGridObservation:
    """Search same-process visible native popup HWNDs for one UIA grid."""
    if os.name != "nt":
        return CustomerLookupGridObservation("unsupported_platform")
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or not 1 <= max_rows <= 25:
        raise ValueError("invalid_customer_grid_limit")

    try:
        from pywinauto import Desktop
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetWindow.restype = wintypes.HWND
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.EnumWindows.argtypes = [
            ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM),
            wintypes.LPARAM,
        ]
        user32.EnumWindows.restype = wintypes.BOOL

        foreground = user32.GetForegroundWindow()
        if not foreground:
            return CustomerLookupGridObservation("no_foreground")
        owner = user32.GetAncestor(foreground, 3) or foreground
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(foreground, ctypes.byref(pid))
        if not pid.value:
            return CustomerLookupGridObservation("no_process_id")
        import psutil
        if psutil.Process(pid.value).name().casefold() != "okna.exe":
            return CustomerLookupGridObservation("wrong_application")

        discovered = []
        seen = set()
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def register(hwnd, _):
            if int(hwnd) in seen or not user32.IsWindowVisible(hwnd):
                return True
            other_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(other_pid))
            if other_pid.value == pid.value:
                seen.add(int(hwnd))
                discovered.append(int(hwnd))
            return len(discovered) < 120

        enum = callback_type(register)
        user32.EnumWindows(enum, 0)
        child_enum = callback_type(register)
        user32.EnumChildWindows.argtypes = [wintypes.HWND, callback_type, wintypes.LPARAM]
        user32.EnumChildWindows(wintypes.HWND(owner), child_enum, 0)

        desktop = Desktop(backend="uia")
        grids = {}
        for hwnd in discovered[:120]:
            try:
                window = desktop.window(handle=hwnd).wrapper_object()
                wrappers = [window, *window.descendants()]
                for item in wrappers:
                    info = item.element_info
                    automation_id = str(getattr(info, "automation_id", "") or "").casefold()
                    role = str(getattr(info, "control_type", "") or "").casefold()
                    visible = bool(getattr(info, "visible", False))
                    if automation_id != "part_gridcontrol" or role not in ("datagrid", "table") or not visible:
                        continue
                    runtime_id = str(getattr(info, "runtime_id", "") or "")
                    if runtime_id:
                        grids[runtime_id] = item
            except Exception:
                continue

        if len(grids) != 1:
            return CustomerLookupGridObservation(
                "grid_not_unique", grid_count=len(grids),
                reason="No unambiguous visible PART_GridControl on WindowHub-owned windows.",
            )
        return _rows_from_grid(next(iter(grids.values())), max_rows=max_rows)
    except Exception as exc:
        return CustomerLookupGridObservation(
            "grid_inspection_failed",
            reason=f"{type(exc).__name__}: {exc}",
        )
