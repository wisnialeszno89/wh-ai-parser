"""Read-only diagnostics for the actual NOWA OFERTA click path.

No model requests, GUI clicks, customer values or document changes.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop


def main():
    print("=== NEW OFFER READ ONLY TRACE ===")
    ok, info = activate_windowhub_workflow_window()
    print("ACTIVATION_OK =", ok)
    # Do not print the actual document title or customer's data.
    if not ok:
        print("STOP: WindowHub could not be activated")
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    stage = stage_of(scene)
    print("STAGE =", stage)
    print("ACTIVE_APP_OK =", (scene.observation.state.active_application or "").casefold().endswith("okna.exe"))
    meta = scene.observation.metadata
    foreground = meta.get("foreground_window_handle", meta.get("window_handle"))
    current_window = meta.get("window_handle")
    print("FOREGROUND_HANDLE_PRESENT =", isinstance(foreground, int) and foreground > 0)
    print("SCENE_WINDOW_HANDLE_PRESENT =", isinstance(current_window, int) and current_window > 0)
    print("FOREGROUND_MATCHES_SCENE =", foreground == current_window)
    print("SCREEN_ORIGIN_PRESENT =", "screen_origin" in meta)
    found = []
    for e in scene.elements:
        if (e.metadata or {}).get("semantic_label") == "NOWA OFERTA" or e.label == "NOWA OFERTA":
            found.append(e)
    print("NEW_OFFER_ELEMENTS =", len(found))
    for i,e in enumerate(found[:5], 1):
        m = e.metadata or {}
        print(f"TARGET_{i}_KIND =", e.kind)
        print(f"TARGET_{i}_SOURCE =", m.get("source"))
        print(f"TARGET_{i}_ENABLED =", m.get("uia_enabled"))
        print(f"TARGET_{i}_VISIBLE =", m.get("uia_visible"))
        print(f"TARGET_{i}_RUNTIME_ID_PRESENT =", bool(m.get("uia_runtime_id")))
        print(f"TARGET_{i}_AUTOMATION_ID_PRESENT =", bool(m.get("automation_id")))
        print(f"TARGET_{i}_INTERACTION =", getattr(e.interaction_capability, "value", None))
        print(f"TARGET_{i}_BOUNDS_VALID =", all(isinstance(v,int) for v in (e.x,e.y,e.width,e.height)) and e.width>0 and e.height>0)
        print(f"TARGET_{i}_BOUNDS =", (e.x,e.y,e.width,e.height))
    print("=== END TRACE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
