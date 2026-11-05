"""Invoke the uniquely identified native NOWA OFERTA button at most once.

Explicit live flags and --execute required. Uses UIA InvokePattern, never
a guessed coordinate, shortcut or fallback click. Reports stage afterward.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider


def resolve_native_control(
    scene, *, label, automation_id=None, allowed_stages=(), desktop=None
):
    """Re-identify a unique native control for an explicitly allowed stage."""
    from pywinauto import Desktop
    if stage_of(scene) not in allowed_stages:
        raise ValueError("unexpected_windowhub_stage")
    meta = scene.observation.metadata
    hwnd = meta.get("window_handle")
    if not isinstance(hwnd, int) or hwnd <= 0:
        raise ValueError("invalid_window_handle")
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    if user32.GetForegroundWindow() != hwnd:
        raise ValueError("windowhub_not_foreground")
    elements = [
        e for e in scene.elements
        if (e.metadata or {}).get("semantic_label", e.label) == label
        and e.kind == "button"
        and (e.metadata or {}).get("source") in
            {"windows_ui_automation", "windowhub_ui_automation"}
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
        and isinstance((e.metadata or {}).get("uia_runtime_id"), str)
        and bool((e.metadata or {}).get("automation_id"))
        and (automation_id is None or
             (e.metadata or {}).get("automation_id") == automation_id)
    ]
    if len(elements) != 1:
        raise ValueError("new_offer_target_not_unique")
    target = elements[0]
    expected = target.metadata or {}
    origin = meta.get("window_rect")
    if origin is None:
        raise ValueError("window_rect_missing")
    expected_rect = (
        int(origin.left) + target.x,
        int(origin.top) + target.y,
        int(origin.left) + target.x + target.width,
        int(origin.top) + target.y + target.height,
    )
    wrappers = (desktop or Desktop(backend="uia")).window(handle=hwnd).wrapper_object().descendants()
    candidates = []
    for wrapper in wrappers:
        try:
            info = wrapper.element_info
            r = wrapper.rectangle()
            rect = (int(r.left), int(r.top), int(r.right), int(r.bottom))
            runtime = WindowHubUIAutomationProvider._runtime_id(wrapper)
            if (
                str(info.control_type).strip().casefold() == "button"
                and info.automation_id == expected["automation_id"]
                and runtime == expected["uia_runtime_id"]
                and rect == expected_rect
                and (info.name or "").strip() == (expected.get("name") or "")
                and bool(info.enabled)
                and bool(info.visible)
            ):
                candidates.append(wrapper)
        except Exception:
            continue
    if len(candidates) != 1:
        raise ValueError("fresh_native_button_identity_mismatch")
    button = candidates[0]
    try:
        invoke = button.iface_invoke
        if invoke is None:
            raise ValueError("uia_invoke_pattern_not_supported")
    except Exception as exc:
        raise ValueError("uia_invoke_pattern_not_supported") from exc
    return invoke


def resolve_native_button(scene, *, desktop=None):
    """Compatibility wrapper for the proven NOWA OFERTA InvokePattern."""
    return resolve_native_control(
        scene, label="NOWA OFERTA",
        allowed_stages=("start", "offer_document"), desktop=desktop,
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Invoke NOWA OFERTA once")
    args = parser.parse_args(argv)
    print("=== WINDOWHUB NATIVE NEW OFFER ===", flush=True)
    if not (os.environ.get("WH_REAL_WINDOWHUB") == "1"
            and os.environ.get("COMPUTER_USE_LIVE") == "1"):
        print("STOP = live authorization required")
        return 2
    ok, _ = activate_windowhub_workflow_window()
    print("AUTO_ACTIVATION =", ok)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    print("BEFORE_STAGE =", stage_of(scene))
    try:
        invoke = resolve_native_button(scene)
    except (ValueError, RuntimeError, OSError) as exc:
        print("STOP = NATIVE_BUTTON_NOT_INVOKABLE", str(exc))
        print("ACTION_TAKEN = NONE")
        return 4
    print("INVOKE_PATTERN_AVAILABLE = True")
    if not args.execute:
        print("ACTION_TAKEN = NONE")
        return 0
    # One attempt, no mouse fallback, no retries if native call returns.
    print("INVOKE_ATTEMPT = 1", flush=True)
    try:
        invoke.Invoke()
    except Exception as exc:
        print("INVOKE_RESULT = EXCEPTION", type(exc).__name__)
        print("RETRY = DISABLED")
        return 6
    print("INVOKE_RETURNED = True")
    for _ in range(4):
        after = enrich_windowhub_scene(loop.observe_scene())
        stage = stage_of(after)
        print("AFTER_STAGE =", stage, flush=True)
        if stage == "document_properties":
            print("RESULT = DOCUMENT_PROPERTIES_REACHED")
            print("FINAL_SAVE = NONE")
            return 0
        if stage is None:
            print("STOP = app_not_foreground")
            return 6
        time.sleep(0.3)
    print("STOP = expected_dialog_not_detected")
    print("RETRY = DISABLED")
    return 6


if __name__ == "__main__":
    raise SystemExit(main())
