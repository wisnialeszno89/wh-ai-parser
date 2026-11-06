"""One targeted read-only probe of the TWO customer lookup edit controls.

No clicks, typing, names, values, screenshots or customer records.
Run while Document Properties is open; focuses WindowHub only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider


def _rectangle(wrapper):
    try:
        r = wrapper.rectangle()
        return (int(r.left), int(r.top), int(r.right), int(r.bottom))
    except Exception:
        return None


def _inside(rect, container):
    return (
        rect is not None and container is not None
        and rect[0] >= container[0] and rect[1] >= container[1]
        and rect[2] <= container[2] and rect[3] <= container[3]
    )


def main():
    print("=== WINDOWHUB CUSTOMER SEARCH TWO-EDIT PROBE (READ ONLY) ===")
    if os.name != "nt" or os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("STOP = Windows and explicit activation flag required")
        return 2
    activated, reason = activate_windowhub_workflow_window()
    print("ACTIVATED =", activated)
    if not activated:
        print("STOP =", reason)
        return 4
    scene = enrich_windowhub_scene(create_windows_desktop_agent_control_loop().observe_scene())
    print("STAGE =", stage_of(scene))
    if stage_of(scene) != "document_properties":
        print("STOP = document properties required")
        return 4
    target = [
        e for e in scene.elements
        if (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
        and (e.metadata or {}).get("uia_visible") is True
    ]
    if len(target) != 1:
        print("STOP = picker not unique")
        return 4
    from pywinauto import Desktop

    hwnd = scene.observation.metadata.get("window_handle")
    root = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    wrappers = [root, *root.descendants()]
    rid = target[0].metadata.get("uia_runtime_id")
    picker = [
        w for w in wrappers
        if (getattr(w.element_info, "automation_id", None) == "IDC_ZAMAWIAJACY"
            and WindowHubUIAutomationProvider._runtime_id(w) == rid)
    ]
    if len(picker) != 1:
        print("STOP = native picker not unique")
        return 4
    picker = picker[0]
    pr = _rectangle(picker)
    nested = set()
    try:
        nested = {WindowHubUIAutomationProvider._runtime_id(w) for w in picker.descendants()}
    except Exception:
        pass
    print("PICKER_RECT =", pr)
    print("PICKER_NATIVE_TYPE =", str(picker.element_info.control_type))
    print("PICKER_NATIVE_CLASS =", str(getattr(picker.element_info, "class_name", ""))[:80])
    print("PICKER_HAS_KEYBOARD_FOCUS =", bool(getattr(picker.element_info, "has_keyboard_focus", False)))

    count = 0
    for w in wrappers:
        try:
            i = w.element_info
            if str(i.control_type).casefold() != "edit" or not i.enabled or not i.visible:
                continue
            rect = _rectangle(w)
            nested_match = WindowHubUIAutomationProvider._runtime_id(w) in nested
            if not nested_match and not _inside(rect, pr):
                continue
            count += 1
            print("CANDIDATE_INDEX =", count)
            print("  AUTOMATION_ID =", str(i.automation_id or "")[:80])
            print("  CLASS =", str(getattr(i, "class_name", "") or "")[:80])
            print("  RECT =", rect)
            print("  STRUCTURAL_CHILD =", nested_match)
            print("  HAS_KEYBOARD_FOCUS =", bool(getattr(i, "has_keyboard_focus", False)))
            print("  VALUE_PATTERN_AVAILABLE =", bool(getattr(w, "iface_value", None)))
            print("  TEXT_PATTERN_AVAILABLE =", bool(getattr(w, "iface_text", None)))
            print("  IS_KEYBOARD_FOCUSABLE =", bool(getattr(i, "is_keyboard_focusable", False)))
            print("  NAME_IS_EMPTY =", not bool(str(i.name or "").strip()))
        except Exception as exc:
            print("CANDIDATE_READ_ERROR =", type(exc).__name__)
    print("TOTAL_CANDIDATES =", count)
    print("ACTION_TAKEN = NONE")
    print("CUSTOMER_VALUES_PRINTED = False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
