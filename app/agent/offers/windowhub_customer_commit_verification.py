"""Verify that a clicked customer suggestion was committed, not merely typed.

A query string in LookUpEdit is not proof of a selected business record.
Native ValuePattern or LegacyIAccessible readback plus no visible dropdown
is one usable corroborated signal after an exact-result click.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerCommitEvidence:
    status: str
    reason: str
    native_exact: bool
    popup_still_contains_exact_result: bool | None


def decide_customer_commit(*, exact_row_was_clicked: bool,
                           native_values: tuple[str, ...],
                           customer_name: str,
                           popup_still_contains_exact_result: bool | None
                           ) -> CustomerCommitEvidence:
    expected = customer_name.strip().casefold()
    values = {v.strip().casefold() for v in native_values if isinstance(v, str) and v.strip()}
    native = expected in values
    if not exact_row_was_clicked:
        return CustomerCommitEvidence("unverified", "no_exact_row_click", native, popup_still_contains_exact_result)
    if not native:
        return CustomerCommitEvidence("unverified", "native_selected_value_not_exposed", False, popup_still_contains_exact_result)
    if popup_still_contains_exact_result is not False:
        return CustomerCommitEvidence("unverified", "dropdown_closure_not_verified", True, popup_still_contains_exact_result)
    return CustomerCommitEvidence("verified", "exact_row_clicked_value_readback_and_popup_closed", True, False)


def verify_clicked_customer_commit(scene, customer_name: str):
    """Post-click UIA readback and exact visual dropdown presence check."""
    from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
    from app.agent.offers.windowhub_customer_visual_selection import (
        _ocr_text_results, match_visual_customer, popup_bounds,
    )
    from PIL import ImageGrab
    import ctypes
    from ctypes import wintypes
    try:
        wrapper = resolve_native_wrapper(
            scene, label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
        )
    except Exception as exc:
        return CustomerCommitEvidence("unverified", "lookup_missing_" + type(exc).__name__, False, None)

    values = []
    try:
        iface = wrapper.iface_value
        if iface is not None:
            value = iface.CurrentValue
            if isinstance(value, str):
                values.append(value)
    except Exception:
        pass
    try:
        info_value = getattr(wrapper.element_info, "value", None)
        if isinstance(info_value, str):
            values.append(info_value)
    except Exception:
        pass
    try:
        name = wrapper.window_text()
        if isinstance(name, str):
            values.append(name)
    except Exception:
        pass
    # Never print a customer's native value to logs.
    r = wrapper.rectangle()
    win = ctypes.WinDLL("user32", use_last_error=True)
    win.GetForegroundWindow.restype = wintypes.HWND
    hwnd = scene.observation.metadata.get("window_handle")
    if int(win.GetForegroundWindow() or 0) != hwnd:
        return CustomerCommitEvidence("unverified", "window_not_foreground", False, None)
    win.GetSystemMetrics.argtypes = [ctypes.c_int]
    win.GetSystemMetrics.restype = ctypes.c_int
    try:
        region = popup_bounds(
            (int(r.left), int(r.top), int(r.right), int(r.bottom)),
            (win.GetSystemMetrics(0), win.GetSystemMetrics(1)),
        )
        lines = _ocr_text_results(ImageGrab.grab(bbox=region, all_screens=False), region)
        popup_match = (len(match_visual_customer(lines, customer_name, region)) > 0
                       if lines is not None else None)
    except Exception:
        popup_match = None
    evidence = decide_customer_commit(
        exact_row_was_clicked=True, native_values=tuple(values),
        customer_name=customer_name, popup_still_contains_exact_result=popup_match,
    )
    print("CUSTOMER_POST_CLICK_NATIVE_EXACT =", evidence.native_exact)
    print("CUSTOMER_POST_CLICK_POPUP_MATCH_PRESENT =", evidence.popup_still_contains_exact_result)
    print("CUSTOMER_POST_CLICK_COMMIT_STATUS =", evidence.status)
    print("CUSTOMER_POST_CLICK_COMMIT_REASON =", evidence.reason)
    return evidence
