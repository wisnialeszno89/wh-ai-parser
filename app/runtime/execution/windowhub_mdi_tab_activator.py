"""Verified native MDI activation for WindowHub document tabs.

This helper is intentionally narrow: it activates one uniquely identified
WindowHub document tab by using the application's MDI relationship, then
verifies both the active MDI child HWND and UI Automation selection state.
Window handles are runtime-only and are never written to persistent knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic, sleep
from typing import Callable


WM_MDIGETACTIVE = 0x0229
WM_MDIACTIVATE = 0x0222


@dataclass(frozen=True, slots=True)
class WindowHubMdiTabActivationResult:
    success: bool
    executed: bool
    target_label: str
    before_selected: bool | None = None
    after_selected: bool | None = None
    active_before_target: bool | None = None
    active_after_target: bool | None = None
    reason: str = ""


def activate_windowhub_mdi_document_tab(
    *,
    target_label: str,
    window_handle: int | None,
    live: bool,
    desktop_factory: Callable[[], object] | None = None,
    message_sender: Callable[[int, int, int, int], int] | None = None,
    foreground_checker: Callable[[int], bool] | None = None,
    sleep_fn: Callable[[float], None] = sleep,
    monotonic_fn: Callable[[], float] = monotonic,
    timeout_seconds: float = 1.5,
) -> WindowHubMdiTabActivationResult:
    """Activate and verify one document tab, or validate it without mutation.

    The caller must already have applied the normal GUI action policy and UIA
    safety gate. This helper adds strict WindowHub/MDI identity and post-action
    verification; it never writes, saves, confirms or submits offer data.
    """
    label = target_label.strip() if isinstance(target_label, str) else ""
    if not label:
        return _failure(label, "Document-tab target label is empty.")
    if not isinstance(window_handle, int) or isinstance(window_handle, bool) or window_handle <= 0:
        return _failure(label, "WindowHub root window handle is unavailable.")
    if timeout_seconds <= 0:
        return _failure(label, "Activation verification timeout must be positive.")

    try:
        desktop = desktop_factory() if desktop_factory is not None else _default_desktop()
        root_spec = desktop.window(handle=window_handle)
        wrapper = getattr(root_spec, "wrapper_object", None)
        root = wrapper() if callable(wrapper) else root_spec
        title_getter = getattr(root, "window_text", None)
        title = title_getter() if callable(title_getter) else ""
        if not isinstance(title, str) or not title.strip().casefold().startswith("okna -"):
            return _failure(label, "Target window is not a verified WindowHub root window.")

        items = tuple(root.descendants())
        tab_matches = [
            item for item in items
            if _control_type(item) == "tabitem"
            and _name(item).casefold() == label.casefold()
            and _is_windowhub_document_tab(item)
        ]
        if len(tab_matches) != 1:
            return _failure(
                label,
                f"Expected exactly one WindowHub document tab; found {len(tab_matches)}.",
            )

        tab = tab_matches[0]
        if not _bool_property(tab, "visible") or not _bool_property(tab, "enabled"):
            return _failure(label, "Document tab is not visible and enabled.")

        # Some legacy WindowHub tab providers do not expose SelectionItemPattern.
        # Native MDI child identity is authoritative when UIA selection state is
        # unavailable; if UIA does expose a boolean, it must agree with MDI.
        selected_before = _selected(tab)

        host = tab.parent()
        mdi_client = host.parent()
        if not _is_mdi_client(mdi_client):
            return _failure(label, "Document tab is not under the expected MDIClient.")

        mdi_handle = _handle(mdi_client)
        if mdi_handle <= 0:
            return _failure(label, "MDIClient native handle is unavailable.")

        child_matches = [
            item for item in items
            if _control_type(item) == "window"
            and _name(item).casefold() == label.casefold()
            and _is_mdi_child_of(item, mdi_handle)
        ]
        if len(child_matches) != 1:
            return _failure(
                label,
                f"Expected exactly one matching MDI child window; found {len(child_matches)}.",
                before_selected=selected_before,
            )

        target_child_handle = _handle(child_matches[0])
        if target_child_handle <= 0:
            return _failure(
                label,
                "Target MDI child native handle is unavailable.",
                before_selected=selected_before,
            )

        send = message_sender or _win32_send_message
        active_before = int(send(mdi_handle, WM_MDIGETACTIVE, 0, 0) or 0)
        if active_before <= 0:
            return _failure(
                label,
                "MDIClient did not report an active document window.",
                before_selected=selected_before,
            )

        active_before_target = active_before == target_child_handle
        if selected_before is not None and active_before_target != selected_before:
            return _failure(
                label,
                "UIA selected state conflicts with the native active MDI document; refusing to guess.",
                before_selected=selected_before,
                active_before_target=active_before_target,
            )

        if active_before_target:
            return WindowHubMdiTabActivationResult(
                success=True,
                executed=False,
                target_label=label,
                before_selected=selected_before,
                after_selected=selected_before,
                active_before_target=True,
                active_after_target=True,
                reason=(
                    "Target document tab is already active in native MDI; "
                    "UIA selection state is unavailable."
                    if selected_before is None
                    else "Target document tab is already active and both state sources agree."
                ),
            )

        if not live:
            return WindowHubMdiTabActivationResult(
                success=True,
                executed=False,
                target_label=label,
                before_selected=selected_before,
                after_selected=selected_before,
                active_before_target=False,
                active_after_target=False,
                reason="DRY_RUN validated the unique tab and its MDI child; no activation was attempted.",
            )

        checker = foreground_checker or _is_foreground_window_or_owned_child
        if not checker(window_handle):
            return _failure(
                label,
                "WindowHub is not the foreground root window; refusing native MDI activation.",
                before_selected=selected_before,
                active_before_target=False,
            )

        # WM_MDIACTIVATE is sent once to the verified MDIClient. The target
        # child handle came from the uniquely matched Window control under
        # that same MDIClient; it is not model-generated or persisted.
        # For WM_MDIACTIVATE sent to the MDIClient, wParam is the child
        # to activate and lParam is unused (must be zero).
        send(mdi_handle, WM_MDIACTIVATE, target_child_handle, 0)

        deadline = monotonic_fn() + timeout_seconds
        last_selected: bool | None = None
        last_active_target = False
        while True:
            active_after = int(send(mdi_handle, WM_MDIGETACTIVE, 0, 0) or 0)
            last_active_target = active_after == target_child_handle
            refreshed = _find_fresh_tab(
                desktop=desktop,
                window_handle=window_handle,
                label=label,
            )
            last_selected = _selected(refreshed) if refreshed is not None else None
            if last_active_target and last_selected is not False:
                return WindowHubMdiTabActivationResult(
                    success=True,
                    executed=True,
                    target_label=label,
                    before_selected=selected_before,
                    after_selected=last_selected,
                    active_before_target=False,
                    active_after_target=True,
                    reason=(
                        "Native MDI activation verified by active child handle; "
                        "UIA selection state is unavailable."
                        if last_selected is None
                        else "Native MDI activation verified by active child handle and UIA selected state."
                    ),
                )
            if monotonic_fn() >= deadline:
                break
            sleep_fn(0.05)

        return WindowHubMdiTabActivationResult(
            success=False,
            executed=True,
            target_label=label,
            before_selected=selected_before,
            after_selected=last_selected,
            active_before_target=False,
            active_after_target=last_active_target,
            reason="MDI activation was sent, but the active child and selected tab did not both verify.",
        )
    except Exception as exc:
        return _failure(
            label,
            f"MDI tab activation failed safely ({type(exc).__name__}); no fallback click was attempted.",
        )


def _default_desktop():
    from app.agent.platform.windows_com import ensure_windows_sta

    ensure_windows_sta()
    from pywinauto import Desktop

    return Desktop(backend="uia")


def _win32_send_message(window_handle: int, message: int, wparam: int, lparam: int) -> int:
    import ctypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send = user32.SendMessageW
    send.argtypes = (
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_size_t,
        ctypes.c_ssize_t,
    )
    send.restype = ctypes.c_void_p
    result = send(
        ctypes.c_void_p(window_handle),
        message,
        wparam,
        lparam,
    )
    return int(result or 0)


def _is_foreground_window_or_owned_child(root_handle: int) -> bool:
    import ctypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    foreground = int(user32.GetForegroundWindow() or 0)
    if foreground == root_handle:
        return True
    if foreground <= 0:
        return False
    root_owner = int(user32.GetAncestor(ctypes.c_void_p(foreground), 3) or 0)
    return root_owner == root_handle


def _find_fresh_tab(*, desktop, window_handle: int, label: str):
    root_spec = desktop.window(handle=window_handle)
    wrapper = getattr(root_spec, "wrapper_object", None)
    root = wrapper() if callable(wrapper) else root_spec
    matches = [
        item for item in root.descendants()
        if _control_type(item) == "tabitem"
        and _name(item).casefold() == label.casefold()
        and _is_windowhub_document_tab(item)
    ]
    return matches[0] if len(matches) == 1 else None


def _is_windowhub_document_tab(item) -> bool:
    try:
        host = item.parent()
        mdi_client = host.parent()
        return (
            _control_type(host) == "tab"
            and "afxtabwnd" in _class_name(host).replace(":", "").casefold()
            and _is_mdi_client(mdi_client)
        )
    except Exception:
        return False


def _is_mdi_client(item) -> bool:
    return _control_type(item) == "pane" and _class_name(item).casefold() == "mdiclient"


def _is_mdi_child_of(item, mdi_handle: int) -> bool:
    try:
        parent = item.parent()
        return _is_mdi_client(parent) and _handle(parent) == mdi_handle
    except Exception:
        return False


def _control_type(item) -> str:
    try:
        return str(getattr(item.element_info, "control_type", "") or "").strip().casefold()
    except Exception:
        return ""


def _class_name(item) -> str:
    try:
        return str(getattr(item.element_info, "class_name", "") or "").strip()
    except Exception:
        return ""


def _name(item) -> str:
    try:
        return str(getattr(item.element_info, "name", "") or "").strip()
    except Exception:
        return ""


def _handle(item) -> int:
    try:
        info = getattr(item, "element_info", None)
        value = getattr(info, "handle", None)
        if value is None:
            value = getattr(item, "handle", None)
            if callable(value):
                value = value()
        return int(value or 0)
    except Exception:
        return 0


def _bool_property(item, attribute: str) -> bool:
    try:
        value = getattr(item.element_info, attribute)
        return value is True or bool(value)
    except Exception:
        return False


def _selected(item) -> bool | None:
    try:
        pattern = getattr(item, "iface_selection_item", None)
        if pattern is not None:
            value = pattern.CurrentIsSelected
            return value if isinstance(value, bool) else None
    except Exception:
        pass
    try:
        getter = getattr(item, "is_selected", None)
        if callable(getter):
            value = getter()
            return value if isinstance(value, bool) else None
    except Exception:
        pass
    return None


def _failure(
    label: str,
    reason: str,
    *,
    before_selected: bool | None = None,
    active_before_target: bool | None = None,
) -> WindowHubMdiTabActivationResult:
    return WindowHubMdiTabActivationResult(
        success=False,
        executed=False,
        target_label=label,
        before_selected=before_selected,
        active_before_target=active_before_target,
        reason=reason,
    )
