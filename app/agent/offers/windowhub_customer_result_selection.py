"""Recognize an exact customer in an open native WindowHub lookup popup.

This is not fuzzy matching: only a visible, enabled and unique exact company
name within the native lookup vicinity can be clicked. Never assume that
text typed into LookUpEdit is a selected business record.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def canonical_customer_name(value: str) -> str:
    """Compare typography-only differences, never omit/reorder identity tokens.

    Top-Trans Janik Artur == Top Trans Janik Artur, but Top-Trans alone
    is NOT equal to the complete customer identity.
    """
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[-‐‑‒–—―]+", " ", value).split())


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
                              picker_rect: tuple[int, int, int, int], *, allow_name_reordering=False) -> list[int]:
    """Return candidate indices only for an exact unique non-editor match."""
    expected = canonical_customer_name(customer_name)
    return [
        i for i, candidate in enumerate(candidates)
        if candidate.visible and candidate.enabled
        and candidate.role.casefold() in SELECTABLE_ROLES
        and customer_identity_matches(
            candidate.name, expected, allow_name_reordering=allow_name_reordering,
        )
        and nearby_lookup(candidate.rect, picker_rect)
        # Text displayed INSIDE the editor is the typed query, not a row.
        and candidate.rect[1] >= picker_rect[3]
    ]


def _rect(wrapper):
    r = wrapper.rectangle()
    return (int(r.left), int(r.top), int(r.right), int(r.bottom))


def customer_name_completes_query(label: str, query: str) -> bool:
    """Match a full-token extension, never a prefix inside a word."""
    label_words = label.casefold().split()
    query_words = query.casefold().split()
    return bool(query_words and len(label_words) > len(query_words)
                and label_words[:len(query_words)] == query_words)


def customer_name_has_reordered_words(label: str, query: str) -> bool:
    """A possible alternative to show the operator, never authority to click."""
    label_words, query_words = label.casefold().split(), query.casefold().split()
    # Preserve the company prefix; allow the rest of the registered name
    # to be ordered differently (for example surname before given name).
    return (
        len(query_words) >= 4 and label_words[:2] == query_words[:2]
        and label_words != query_words and sorted(label_words[2:]) == sorted(query_words[2:])
    )


def customer_identity_matches(label, expected, *, allow_name_reordering=False) -> bool:
    actual = canonical_customer_name(label)
    expected = canonical_customer_name(expected)
    return bool(expected) and (
        actual == expected
        or (allow_name_reordering and customer_name_has_reordered_words(actual, expected))
    )



def _customer_name_is_suggestion(label: str, query: str) -> bool:
    return customer_name_completes_query(label, query) or customer_name_has_reordered_words(label, query)


def select_exact_customer_result(scene, customer_name: str, *, visible_completions=None,
                                 strictly_owned=False, allow_name_reordering=False,
                                 authorization=None) -> tuple[bool, str]:
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
            exact_customer_picker_id=True,
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
    if strictly_owned:
        from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
        from app.agent.runtime.windowhub_new_offer_handoff import owner_chain

        api = _Win32Mdi()
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
                if process.value == expected_pid.value and (
                    not strictly_owned or hwnd in owner_chain(win_hwnd, api)
                ):
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
                if strictly_owned and window is document:
                    ancestor = info.parent
                    for _ in range(12):
                        if ancestor is None:
                            break
                        if ancestor.automation_id == "IDC_ZAMAWIAJACY":
                            break
                        ancestor = ancestor.parent
                    else:
                        ancestor = None
                    if ancestor is None:
                        continue
                name = str(info.name or "").strip()
                if not customer_identity_matches(
                    name, customer_name, allow_name_reordering=allow_name_reordering,
                ) and not (
                    visible_completions is not None
                    and _customer_name_is_suggestion(name, customer_name)
                ):
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

    if visible_completions is not None:
        for _, candidate in candidates:
            name = candidate.name
            if (
                candidate.visible and candidate.enabled
                and candidate.rect[1] >= picker_rect[3]
                and nearby_lookup(candidate.rect, picker_rect)
                and _customer_name_is_suggestion(name, customer_name)
            ):
                visible_completions.add(name)

    accepted = exact_customer_candidates(
        [item[1] for item in candidates], customer_name, picker_rect,
        allow_name_reordering=allow_name_reordering,
    )
    print("CUSTOMER_EXACT_VISIBLE_MATCHES =", sum(
        canonical_customer_name(item[1].name) == canonical_customer_name(customer_name) for item in candidates
    ))
    print("CUSTOMER_EXACT_NEARBY_RESULTS =", len(accepted))
    if len(accepted) > 1:
        return False, "EXACT_CUSTOMER_RESULT_AMBIGUOUS"
    if not accepted:
        return False, "EXACT_CUSTOMER_RESULT_NOT_UNIQUE_OR_NOT_VISIBLE"
    node = candidates[accepted[0]][0]
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    if int(user32.GetForegroundWindow() or 0) != hwnd:
        return False, "CUSTOMER_DOCUMENT_NOT_FOREGROUND"
    if authorization is not None and not authorization():
        return False, "CUSTOMER_AUTHORIZATION_REVOKED"
    try:
        node.click_input()
    except Exception as exc:
        return False, "CUSTOMER_RESULT_CLICK_FAILED_" + type(exc).__name__
    return True, "EXACT_CUSTOMER_RESULT_CLICKED_PENDING_DOCUMENT_VERIFICATION"


def reveal_customer_results(scene) -> tuple[bool, str]:
    """Open one verified customer lookup dropdown, without selecting a row."""
    from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
    try:
        picker = resolve_native_wrapper(
            scene, label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            exact_customer_picker_id=True,
        )
        rect = picker.rectangle()
        if (str(picker.element_info.class_name).casefold() != "lookupedit"
                or int(rect.width()) < 80 or int(rect.height()) < 16):
            return False, "CUSTOMER_DROPDOWN_INVALID"
        # Click only the arrow portion of the exact control, verified via
        # native element identity. No item is selected or accepted here.
        from pywinauto import mouse
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        expected = scene.observation.metadata.get("window_handle")
        if not isinstance(expected, int) or int(user32.GetForegroundWindow() or 0) != expected:
            return False, "CUSTOMER_DOCUMENT_NOT_FOREGROUND"
        mouse.click(coords=(int(rect.right) - 10,
                            (int(rect.top) + int(rect.bottom)) // 2))
        return True, "CUSTOMER_DROPDOWN_OPEN_ATTEMPTED"
    except Exception as exc:
        return False, "CUSTOMER_DROPDOWN_" + type(exc).__name__
