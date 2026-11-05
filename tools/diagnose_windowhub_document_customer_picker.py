"""Passive, data-redacted inspection of the existing customer picker button.

No model requests, mouse, keyboard, native Invoke or document writes.
Automatically focuses the existing WindowHub workflow window.
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

TARGET_ID = "IDC_ZAMAWIAJACY"


def main():
    print("=== DOCUMENT CUSTOMER PICKER GUARD TRACE ===", flush=True)
    if not (os.getenv("WH_REAL_WINDOWHUB") == "1" and
            os.getenv("COMPUTER_USE_LIVE") == "1"):
        print("STOP = live window activation authorization required")
        return 2
    ok, _ = activate_windowhub_workflow_window()
    print("AUTO_ACTIVATION =", ok)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    stage = stage_of(scene)
    print("STAGE =", stage)
    if stage != "document_properties":
        print("STOP = document_properties_not_active")
        print("ACTION_TAKEN = NONE")
        return 4

    observed = [e for e in scene.elements
                if (e.metadata or {}).get("automation_id") == TARGET_ID]
    print("MATCHING_UIA_CONTROL_COUNT =", len(observed))
    for idx, element in enumerate(observed[:4], 1):
        metadata = element.metadata or {}
        print(f"CONTROL_{idx}_TYPE =", element.kind)
        print(f"CONTROL_{idx}_SEMANTIC_LABEL_MATCH =",
              metadata.get("semantic_label") == "Wybierz istniejącego klienta")
        print(f"CONTROL_{idx}_VISIBLE =", metadata.get("uia_visible"))
        print(f"CONTROL_{idx}_ENABLED =", metadata.get("uia_enabled"))
        print(f"CONTROL_{idx}_RUNTIME_ID_PRESENT =", bool(metadata.get("uia_runtime_id")))
        print(f"CONTROL_{idx}_NATIVE_NAME_PRESENT =", bool(metadata.get("name")))

    if len(observed) != 1:
        print("STOP = customer_picker_not_unique_in_scene")
        print("ACTION_TAKEN = NONE")
        return 4
    expected = observed[0]
    m = expected.metadata or {}
    rect = scene.observation.metadata.get("window_rect")
    hwnd = scene.observation.metadata.get("window_handle")
    if rect is None or not isinstance(hwnd, int):
        print("STOP = window_geometry_missing")
        return 4
    bounds = (
        rect.left + expected.x, rect.top + expected.y,
        rect.left + expected.x + expected.width,
        rect.top + expected.y + expected.height,
    )
    from pywinauto import Desktop
    wrappers = Desktop(backend="uia").window(handle=hwnd).wrapper_object().descendants()
    id_matches = runtime_matches = geometry_matches = name_matches = invoke_supported = 0
    for wrapper in wrappers:
        try:
            info = wrapper.element_info
            if info.automation_id != TARGET_ID:
                continue
            id_matches += 1
            if WindowHubUIAutomationProvider._runtime_id(wrapper) != m.get("uia_runtime_id"):
                continue
            runtime_matches += 1
            r = wrapper.rectangle()
            if (int(r.left), int(r.top), int(r.right), int(r.bottom)) != bounds:
                continue
            geometry_matches += 1
            if (info.name or "").strip() != (m.get("name") or ""):
                continue
            name_matches += 1
            try:
                if wrapper.iface_invoke is not None:
                    invoke_supported += 1
            except Exception:
                pass
        except Exception:
            continue
    print("NATIVE_AUTOMATION_ID_MATCHES =", id_matches)
    print("NATIVE_RUNTIME_ID_MATCHES =", runtime_matches)
    print("NATIVE_RECT_MATCHES =", geometry_matches)
    print("NATIVE_NAME_MATCHES =", name_matches)
    print("NATIVE_INVOKE_SUPPORTED =", invoke_supported)
    print("ACTION_TAKEN = NONE")
    print("MODEL_REQUESTS = 0")
    print("=== END TRACE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
