"""Observe the actual WH Okna catalogue wizard by HWND without focus change.

Never activate a window, press keys, expand a list, access SQL or save a
document. In production, HWND/process identity is checked with Win32 again
after inventory capture, preventing stale handles from being rebound.
"""
from __future__ import annotations

import os

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene


def _verified_native_window(hwnd: int, expected_title: str) -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        if not user32.IsWindow(wintypes.HWND(hwnd)):
            return False
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(
            wintypes.HWND(hwnd), ctypes.byref(pid),
        )
        if pid.value <= 0:
            return False
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        actual = WindowsDesktopEnvironmentAdapter._process_name(
            kernel32, int(pid.value),
        )
        if (actual or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe":
            return False
        # Snapshot text must remain identical; modal/popup transitions
        # are refused rather than retargeting another WindowHub document.
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(wintypes.HWND(hwnd), buf, len(buf))
        return buf.value == expected_title
    except Exception:
        return False


def read_catalogue_window_without_focus(
    *, inventory=None, provider=None, native_verifier=None,
) -> tuple[ScreenScene | None, str]:
    """Return one exactly identified wizard scene, or a safe failure code.

    When tests inject inventory/provider, a verifier must be explicitly
    supplied too. Production always uses fresh native process validation.
    """
    from app.agent.offers.windowhub_offer_form_map import (
        identify_windowhub_form_step,
    )
    from app.agent.runtime.navimind_background_windowhub_reader import (
        _is_windowhub,
    )
    if inventory is None:
        if os.name != "nt":
            return None, "local_windows_required"
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        desktop = WindowsDesktopEnvironmentAdapter()
        foreground = desktop._capture_foreground_window()
        inventory = desktop._capture_visible_windows(
            foreground.handle, snapshot=foreground,
        )
        verifier = _verified_native_window
    else:
        if not callable(native_verifier):
            return None, "injected_inventory_verifier_missing"
        verifier = native_verifier
    candidates = [
        w for w in inventory
        if _is_windowhub(w)
        and isinstance(w.title, str)
        and identify_windowhub_form_step(w.title) is not None
        and getattr(w, "rect", None) is not None
    ]
    if len(candidates) != 1:
        return None, (
            "catalogue_wizard_not_found" if not candidates
            else "multiple_catalogue_wizards_ambiguous"
        )
    target = candidates[0]
    if not verifier(target.handle, target.title):
        return None, "windowhub_native_process_or_title_changed"
    if provider is None:
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )
        provider = WindowHubUIAutomationProvider()
    obs = EnvironmentObservation(
        state=EnvironmentState(
            active_application="Okna.exe",
            active_window_title=target.title,
        ),
        metadata={
            "window_handle": target.handle,
            "window_rect": target.rect,
        },
    )
    try:
        elements = tuple(provider.perceive(obs))
    except Exception:
        return None, "windowhub_catalogue_uia_unavailable"
    if not verifier(target.handle, target.title):
        return None, "windowhub_native_process_changed_during_scan"
    return ScreenScene(obs, elements=elements), "native_catalogue_wizard_read_only"
