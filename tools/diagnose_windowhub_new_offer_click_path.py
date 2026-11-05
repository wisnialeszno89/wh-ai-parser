"""Read-only WindowHub new-offer target and window-state diagnostics.

No foreground activation, GUI actions, HTTP requests or customer values.
"""
from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop


def window_inventory():
    if os.name != "nt":
        print("WINDOWS_REQUIRED = True")
        return False

    import psutil

    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    foreground = user32.GetForegroundWindow()

    processes = {
        p.info["pid"] for p in psutil.process_iter(["pid", "name"])
        if (p.info["name"] or "").casefold() == "okna.exe"
    }
    print("OKNA_PROCESS_COUNT =", len(processes))
    visible = []
    CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def inspect(hwnd, unused):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value not in processes or not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        name = buf.value
        if name == "Właściwości dokumentu":
            stage = "document_properties"
        elif name.startswith("Okna - OFR/"):
            stage = "offer_document"
        elif name.startswith("Okna - Start1"):
            stage = "start"
        elif name in {"Dodawanie nowej pozycji", "Zakładanie nowego klienta"}:
            stage = "workflow_dialog"
        elif name:
            stage = "other_named_window"
        else:
            stage = "untitled"
        visible.append((stage, hwnd == foreground))
        return True

    callback = CALLBACK(inspect)
    user32.EnumWindows(callback, 0)
    print("VISIBLE_WINDOW_COUNT =", len(visible))
    for i, (stage, active) in enumerate(visible, 1):
        print(f"VISIBLE_{i}_STAGE =", stage)
        print(f"VISIBLE_{i}_FOREGROUND =", active)
    return any(active for _, active in visible)


def main():
    print("=== NEW OFFER READ ONLY TRACE ===")
    is_foreground = window_inventory()
    print("WINDOWHUB_FOREGROUND =", is_foreground)
    if not is_foreground:
        print("TARGET_INSPECTION_SKIPPED = foreground is not Okna.exe")
        print("ACTION_TAKEN = NONE")
        return 0

    # Foreground belongs to Okna.exe. Observe once without taking control.
    scene = enrich_windowhub_scene(
        create_windows_desktop_agent_control_loop().observe_scene()
    )
    print("SCENE_STAGE =", stage_of(scene))
    found = [
        e for e in scene.elements
        if e.label == "NOWA OFERTA"
        or (e.metadata or {}).get("semantic_label") == "NOWA OFERTA"
    ]
    print("NEW_OFFER_ELEMENT_COUNT =", len(found))
    for i, element in enumerate(found[:5], 1):
        meta = element.metadata or {}
        print(f"TARGET_{i}_KIND =", element.kind)
        print(f"TARGET_{i}_SOURCE =", meta.get("source"))
        print(f"TARGET_{i}_VISIBLE =", meta.get("uia_visible"))
        print(f"TARGET_{i}_ENABLED =", meta.get("uia_enabled"))
        print(f"TARGET_{i}_RUNTIME_ID_PRESENT =", bool(meta.get("uia_runtime_id")))
        print(f"TARGET_{i}_INTERACTION =", getattr(element.interaction_capability, "value", None))
        print(f"TARGET_{i}_BOUNDS_VALID =", all(
            isinstance(v, int) for v in
            (element.x, element.y, element.width, element.height)
        ) and element.width > 0 and element.height > 0)
    print("ACTION_TAKEN = NONE")
    print("=== END TRACE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
