"""Recognize an exact customer in an open native WindowHub lookup popup.

This is not fuzzy matching: only a visible, enabled and unique exact company
name within the native lookup vicinity can be clicked. Never assume that
text typed into LookUpEdit is a selected business record.
"""
from __future__ import annotations

from dataclasses import dataclass


SELECTABLE_ROLES = frozenset({"dataitem", "listitem", "treeitem", "text", "custom"})


@dataclass(frozen=True)
class Candidate:
    role: str
    name: str
    rect: tuple[int, int, int, int]
    enabled: bool = True
    visible: bool = True


def nearby_lookup(rect: tuple[int, int, int, int], picker: tuple[int, int, int, int]) -> bool:
    """Bound potential DevExpress dropdown to the customer field neighborhood."""
    left, top, right, bottom = rect
    pl, pt, pr, pb = picker
    return (
        right > left and bottom > top
        and left < pr + 300 and right > pl - 160
        and top >= pt - 70 and top < pb + 580
    )


def exact_customer_candidates(candidates: list[Candidate], customer_name: str,
                              picker_rect: tuple[int, int, int, int]) -> list[int]:
    """Return candidate indices only for an exact unique non-editor match."""
    expected = customer_name.strip().casefold()
    return [
        i for i, candidate in enumerate(candidates)
        if candidate.visible and candidate.enabled
        and candidate.role.casefold() in SELECTABLE_ROLES
        and candidate.name.strip().casefold() == expected
        and nearby_lookup(candidate.rect, picker_rect)
        # Text displayed INSIDE the editor is the typed query, not a row.
        and candidate.rect[1] >= picker_rect[3]
    ]


def _rect(wrapper):
    r = wrapper.rectangle()
    return (int(r.left), int(r.top), int(r.right), int(r.bottom))


def select_exact_customer_result(scene, customer_name: str) -> tuple[bool, str]:
    """Observe visible same-process UIA trees, then click one exact result.

    A popup may be a direct/indirect owner of Document Properties, not a direct
    child HWND. Scan top-level same-process windows, but accept only rows
    spatially adjacent to the observed customer LookupEdit.
    """
    hwnd = scene.observation.metadata.get("window_handle")
    if not isinstance(hwnd, int) or hwnd <= 0:
        return False, "DOCUMENT_WINDOW_MISSING"
    from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
    try:
        picker = resolve_native_wrapper(
            scene, label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
        )
        picker_rect = _rect(picker)
    except Exception as exc:
        return False, "PICKER_NOT_VERIFIED_" + type(exc).__name__

    import ctypes
    from ctypes import wintypes
    from pywinauto import Desktop
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    expected_pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(expected_pid))
    if not expected_pid.value:
        return False, "DOCUMENT_PROCESS_NOT_VERIFIED"

    desktop = Desktop(backend="uia")
    windows = []
    try:
        document = desktop.window(handle=hwnd).wrapper_object()
        windows.append(document)
        # Prefer the verified document tree; include other top-level windows
        # of the same process because DevExpress sometimes uses a popup HWND.
        for window in desktop.windows():
            try:
                win_hwnd = int(window.handle)
                if win_hwnd == hwnd or not window.is_visible():
                    continue
                process = wintypes.DWORD()
                user32.GetWindowThreadProcessId(win_hwnd, ctypes.byref(process))
                if process.value == expected_pid.value:
                    windows.append(window)
            except Exception:
                continue
    except Exception as exc:
        return False, "WINDOW_SCAN_FAILED_" + type(exc).__name__

    candidates = []
    seen = set()
    for window in windows:
        try:
            descendants = window.descendants()
        except Exception:
            continue
        for node in descendants:
            try:
                info = node.element_info
                role = str(info.control_type or "").casefold()
                if role not in SELECTABLE_ROLES:
                    continue
                name = str(info.name or "").strip()
                if name.casefold() != customer_name.strip().casefold():
                    continue
                rect = _rect(node)
                key = (role, name.casefold(), rect)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append((node, Candidate(
                    role, name, rect, bool(info.enabled), bool(info.visible),
                )))
            except Exception:
                continue

    accepted = exact_customer_candidates(
        [item[1] for item in candidates], customer_name, picker_rect
    )
    print("CUSTOMER_EXACT_VISIBLE_MATCHES =", len(candidates))
    print("CUSTOMER_EXACT_NEARBY_RESULTS =", len(accepted))
    if len(accepted) != 1:
        return False, "EXACT_CUSTOMER_RESULT_NOT_UNIQUE_OR_NOT_VISIBLE"
    node = candidates[accepted[0]][0]
    try:
        node.click_input()
    except Exception as exc:
        return False, "CUSTOMER_RESULT_CLICK_FAILED_" + type(exc).__name__
    return True, "EXACT_CUSTOMER_RESULT_CLICKED_PENDING_DOCUMENT_VERIFICATION"
