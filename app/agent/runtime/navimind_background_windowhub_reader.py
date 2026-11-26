"""Bounded, content-free inspection of WindowHub UIA in the current desktop.

Does not activate a HWND or capture the screen. Unlike the ordinary foreground
scene reader, uses the exact HWND from the Windows inventory to inspect a
background window. Window text is used locally only for stage classification;
customer fields, values, labels, titles and HWNDs are not exported.
"""
from __future__ import annotations

import os
from typing import Callable


def _is_windowhub(window) -> bool:
    process = getattr(window, "application", "") or ""
    basename = process.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    return (
        basename == "okna.exe"
        and getattr(window, "is_visible", False) is True
        and getattr(window, "is_minimized", False) is False
        and type(getattr(window, "handle", None)) is int
        and window.handle > 0
    )


def safe_stage(title: str | None) -> str:
    """Stage only; no user/customer/offer text leaks into the model."""
    if not title:
        return "unknown"
    from app.agent.learning.windowhub_demonstration import KNOWN_STAGES
    clean = title.strip().casefold()
    if clean.startswith("okna - ofr/"):
        return "offer_document"
    if clean.startswith("okna - zlc/"):
        return "order_document"
    return KNOWN_STAGES.get(clean, "unmapped")


def inspect_windowhub_background(
    *,
    inventory=None,
    desktop_factory: Callable[[], object] | None = None,
) -> str:
    """Read UIA control counts by verified HWND, without keyboard or mouse.

    No screenshots. If any target cannot be verified against the Windows
    inventory and UIA's own process name, return a bounded diagnostic rather
    than implying the WindowHub document is readable.
    """
    if inventory is None:
        if os.name != "nt":
            return "Odczyt WindowHub wymaga lokalnej sesji Windows."
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        adapter = WindowsDesktopEnvironmentAdapter()
        foreground = adapter._capture_foreground_window()
        inventory = adapter._capture_visible_windows(
            foreground.handle, snapshot=foreground,
        )
    candidates = [w for w in inventory if _is_windowhub(w)]
    if not candidates:
        minimized = [
            w for w in inventory
            if ((getattr(w, "application", "") or "").replace("\\", "/")
                .rsplit("/", 1)[-1].casefold() == "okna.exe")
            and getattr(w, "is_visible", False) is True
            and getattr(w, "is_minimized", False) is True
        ]
        if minimized:
            return (
                "WindowHub działa, ale jego okno jest zminimalizowane. "
                "Nie mogę wiarygodnie odczytać kontrolek UIA w tym stanie. "
                "Mogę kontynuować analizę zapytania i przygotowanie planu "
                "bez przywracania okna. Po osobnym lokalnym Wznów pracę "
                "i włączeniu LIVE wykonawca może spróbować sam przywrócić "
                "jednoznacznie zweryfikowane okno; Windows może odmówić "
                "przejęcia fokusu. Nie kliknąłem ani niczego nie zapisałem."
            )
        return (
            "Nie znalazłem niezminimalizowanego okna WindowHub. "
            "Mogę nadal analizować zapytanie i przygotować plan, lecz "
            "do interakcji z programem potrzebuję jego jednoznacznej "
            "identyfikacji. Niczego nie zmieniono."
        )
    # Observe a small number of HWNDs, never a whole desktop. Native controls
    # can be expensive to inspect inside WindowHub's legacy MDI.
    if len(candidates) > 3:
        return (
            "WindowHub ma zbyt wiele równocześnie widocznych okien do "
            "jednoznacznego odczytu. Nie wykonałem żadnej akcji."
        )

    try:
        if desktop_factory is None:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
        else:
            desktop = desktop_factory()
    except Exception:
        return "Interfejs UIA nie jest dostępny. Programu nie zmieniono."

    import ctypes
    from ctypes import wintypes
    verified = []
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        for w in candidates:
            # Verify the HWND still belongs to okna.exe before reading UIA,
            # rather than using a stale inventory handle for another process.
            if os.name == "nt" and desktop_factory is None:
                # Production uses native HWND/process identity checks. An
                # explicitly injected test desktop has synthetic handles and
                # must be validated against its injected UIA root instead.
                user32 = ctypes.WinDLL("user32", use_last_error=True)
                is_window = user32.IsWindow
                is_window.argtypes = (wintypes.HWND,)
                is_window.restype = wintypes.BOOL
                if not is_window(w.handle):
                    continue
                pid = wintypes.DWORD()
                get_pid = user32.GetWindowThreadProcessId
                get_pid.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
                get_pid.restype = wintypes.DWORD
                get_pid(w.handle, ctypes.byref(pid))
                actual = WindowsDesktopEnvironmentAdapter._process_name(
                    kernel32, int(pid.value),
                )
                if (actual or "").casefold() != "okna.exe":
                    continue
            root = desktop.window(handle=w.handle).wrapper_object()
            # Fresh title check detects MDI window switches and avoids
            # silently attributing content to a stale inventory snapshot.
            if root.window_text() != (w.title or ""):
                continue
            # Limit traversal depth for background safety; structure only.
            nodes = tuple(root.descendants(depth=3))[:250]
            controls = 0
            for node in nodes:
                try:
                    info = node.element_info
                    if getattr(info, "visible", True) is not True:
                        continue
                    if getattr(info, "control_type", None) in (
                        "Button", "Edit", "ComboBox", "CheckBox", "TabItem",
                        "MenuItem", "ListItem", "RadioButton", "TreeItem",
                    ):
                        controls += 1
                except Exception:
                    continue
            verified.append((safe_stage(w.title), controls))
    except Exception:
        return (
            "Nie udało się odczytać struktury WindowHub działającego w tle. "
            "Nie przełączałem okien i niczego nie zmieniłem."
        )
    if not verified:
        return (
            "Wykryłem WindowHub, ale nie potwierdziłem jego aktualnego "
            "okna UIA. Nie odczytałem zawartości oferty i niczego nie zmieniłem."
        )
    if len(verified) > 1:
        unique_stages = sorted(set(stage for stage, _ in verified))
        stage = unique_stages[0] if len(unique_stages) == 1 else "multiple_windows"
    else:
        stage = verified[0][0]
    total = sum(count for _, count in verified)
    # The aggregate UIA count is not a unique document or safe native
    # interaction target. Never imply otherwise when multiple HWNDs exist.
    scope = (
        "Wykryto wiele okien WindowHub; nie potrafię na podstawie tego "
        "ograniczonego odczytu jednoznacznie przypisać kontrolek do "
        "właściwego dokumentu. Wymagana osobna weryfikacja zakresu "
        "przed sterowaniem."
        if len(verified) > 1 else
        "Jedno okno UIA zweryfikowane; nie oznacza to potwierdzenia "
        "aktywnej oferty ani uprawnienia do sterowania."
    )
    return (
        "Odczytałem strukturę WindowHub przez UIA bez przełączania aktywnego "
        "okna. Etap: " + stage + "; sprawdzone okna: "
        + str(len(verified)) + "; kontrolki interaktywne (ograniczona "
        "głębokość): " + str(total)
        + ". " + scope
        + " Nie odczytałem wartości oferty, nie kliknąłem ani niczego nie zapisałem."
    )
