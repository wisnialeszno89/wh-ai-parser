"""Read-only, one-shot observation of foreground WindowHub with no pinned OFR.

No keyboard, pointer input, document edits or model requests. Only bounded
stage and generic UIA metadata is emitted, never customer values or titles.
"""
from __future__ import annotations

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def locate_windowhub_windows(windows) -> tuple[str, ...]:
    """Find WindowHub among visible top-level windows without activating any.

    Do not disclose window titles, handles, paths or other application names.
    This proves discovery only; it cannot verify WindowHub UIA while hidden.
    """
    found = []
    for window in windows:
        process = getattr(window, "application", "") or ""
        process = process.replace("\\", "/").rsplit("/", 1)[-1].casefold()
        if process != "okna.exe" or getattr(window, "is_visible", False) is not True:
            continue
        found.append(window)
    if not found:
        return ("WINDOWHUB_DISCOVERY=NOT_FOUND", "WINDOWHUB_FOUND_WINDOWS=0",
                "WINDOWHUB_NATIVE_ACTIONS=0")
    foreground = any(getattr(w, "is_foreground", False) is True for w in found)
    minimized = all(getattr(w, "is_minimized", False) is True for w in found)
    return (
        "WINDOWHUB_DISCOVERY=FOUND",
        "WINDOWHUB_FOUND_WINDOWS=" + str(min(len(found), 64)),
        "WINDOWHUB_IS_FOREGROUND=" + str(foreground),
        "WINDOWHUB_ALL_MINIMIZED=" + str(minimized),
        "WINDOWHUB_NATIVE_ACTIONS=0",
    )


def run_discovery(*, inventory=None, output=print) -> int:
    """One Win32 window inventory. Does not capture the screen or steal focus."""
    if inventory is None and os.name != "nt":
        output("WINDOWHUB_DISCOVERY=WINDOWS_REQUIRED")
        return 2
    try:
        if inventory is None:
            from app.agent.environment.windows_desktop_environment_adapter import (
                WindowsDesktopEnvironmentAdapter,
            )
            adapter = WindowsDesktopEnvironmentAdapter()
            foreground = adapter._capture_foreground_window()
            inventory = adapter._capture_visible_windows(
                foreground.handle, snapshot=foreground,
            )
        for line in locate_windowhub_windows(inventory):
            output(line)
        return 0
    except Exception:
        output("WINDOWHUB_DISCOVERY=FAILED")
        output("WINDOWHUB_NATIVE_ACTIONS=0")
        return 1


def diagnose_uia_root(scene, *, desktop_factory=None) -> tuple[str, ...]:
    """Read-only root diagnostics, reporting no window titles, IDs or values.

    Existing generic UIA provider silently returns () for missing pywinauto,
    wrong foreground handle, mismatched window title and traversal failure.
    This diagnostic separates the first three without clicking or reading
    descendants, so it is safe even with large WindowHub MDI trees.
    """
    metadata = getattr(scene.observation, "metadata", None) or {}
    hwnd = metadata.get("window_handle")
    if type(hwnd) is not int or hwnd <= 0:
        return ("WINDOWHUB_UIA_ROOT=HANDLE_MISSING",)
    try:
        if desktop_factory is None:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
        else:
            desktop = desktop_factory()
    except ImportError:
        return ("WINDOWHUB_UIA_ROOT=PYWINAUTO_MISSING",)
    except Exception:
        return ("WINDOWHUB_UIA_ROOT=DESKTOP_UNAVAILABLE",)
    try:
        window = desktop.window(handle=hwnd).wrapper_object()
    except Exception as exc:
        return ("WINDOWHUB_UIA_ROOT=LOOKUP_FAILED",
                "WINDOWHUB_UIA_ERROR_TYPE=" + type(exc).__name__)
    try:
        same_title = window.window_text() == (
            scene.observation.state.active_window_title or ""
        )
    except Exception as exc:
        return ("WINDOWHUB_UIA_ROOT=TITLE_READ_FAILED",
                "WINDOWHUB_UIA_ERROR_TYPE=" + type(exc).__name__)
    return (
        "WINDOWHUB_UIA_ROOT=REACHABLE",
        "WINDOWHUB_UIA_TITLE_MATCH=" + str(same_title),
        "WINDOWHUB_UIA_ROOT_ACTIONS=0",
    )


def summarize_uia_visibility(scene) -> tuple[str, ...]:
    """Safe provider counts; zero mapped controls need not mean zero UIA objects.

    Do not emit labels, customer names, HWNDs, runtime IDs or coordinates.
    These counts diagnose whether provider traversal or the strict mapping
    excluded visible Start1 controls.
    """
    elements = getattr(scene, "elements", ()) or ()
    uia_sources = {"windows_ui_automation", "windowhub_ui_automation"}
    native = 0
    visible = 0
    enabled = 0
    interactive = 0
    with_id = 0
    mapped_id = 0
    roles = {"button", "edit", "checkbox", "combobox", "radiobutton", "tabitem"}
    for item in elements:
        meta = getattr(item, "metadata", None) or {}
        if meta.get("source") not in uia_sources:
            continue
        native += 1
        if meta.get("uia_visible") is not True:
            continue
        visible += 1
        if meta.get("uia_enabled") is True:
            enabled += 1
        if getattr(item, "kind", None) in roles:
            interactive += 1
            identifier = meta.get("automation_id")
            if isinstance(identifier, str) and identifier.strip():
                with_id += 1
                if identifier.startswith("IDC_") or identifier.isdecimal():
                    mapped_id += 1
    return (
        "WINDOWHUB_UIA_ELEMENTS=" + str(native),
        "WINDOWHUB_UIA_VISIBLE=" + str(visible),
        "WINDOWHUB_UIA_ENABLED_VISIBLE=" + str(enabled),
        "WINDOWHUB_UIA_INTERACTIVE_VISIBLE=" + str(interactive),
        "WINDOWHUB_UIA_INTERACTIVE_WITH_ID=" + str(with_id),
        "WINDOWHUB_UIA_INTERACTIVE_MAPPED_ID=" + str(mapped_id),
    )


def describe_windowhub_scene(scene) -> tuple[str, ...]:
    from app.agent.learning.windowhub_demonstration import stage_of, semantic_snapshot
    try:
        state = scene.observation.state
        process = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
        if process != "okna.exe":
            return ("WINDOWHUB_FOREGROUND=False", "WINDOWHUB_STAGE=not_foreground")
        stage = stage_of(scene)
        known = {
            "start", "document_properties", "new_customer", "position",
            "dimensions", "basic_parameters", "glazing", "hardware",
            "modifier", "offer_document", "order_document", "windowhub_unmapped",
        }
        stage = stage if stage in known else "unmapped"
        snapshot = semantic_snapshot(scene)
        control_count = len(snapshot.get("controls", {})) if isinstance(snapshot, dict) else 0
        return (
            "WINDOWHUB_FOREGROUND=True",
            "WINDOWHUB_STAGE=" + stage,
            "WINDOWHUB_SAFE_UIA_CONTROLS=" + str(min(control_count, 150)),
            *summarize_uia_visibility(scene),
            "WINDOWHUB_DOCUMENT_CONTENT_EXPORTED=False",
            "WINDOWHUB_NATIVE_ACTIONS=0",
        )
    except Exception:
        return ("WINDOWHUB_INSPECT=UNREADABLE", "WINDOWHUB_NATIVE_ACTIONS=0")


def run_inspection(*, observe=None, output=print) -> int:
    if observe is None and os.name != "nt":
        output("WINDOWHUB_INSPECT=WINDOWS_REQUIRED")
        return 2
    output("WINDOWHUB_INSPECT=REQUEST_STARTED")
    try:
        if observe is None:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                # Defense in depth: force dry-run even if shell requested LIVE.
                os.environ["COMPUTER_USE_LIVE"] = "0"
                from app.agent.runtime.windows_desktop_agent_control_loop import (
                    create_windows_desktop_agent_control_loop,
                )
                scene = create_windows_desktop_agent_control_loop().observe_scene()
            finally:
                pythoncom.CoUninitialize()
        else:
            scene = observe()
    except Exception:
        output("WINDOWHUB_INSPECT=OBSERVATION_FAILED")
        output("WINDOWHUB_NATIVE_ACTIONS=0")
        return 1
    lines = describe_windowhub_scene(scene)
    for line in lines:
        output(line)
    if observe is None and "WINDOWHUB_FOREGROUND=True" in lines:
        for line in diagnose_uia_root(scene):
            output(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_inspection())
