"""Read-only diagnostic for customer-picker capability in live WindowHub.

Only prints whitelisted control metadata; never prints values, customer names or
native runtime identifiers. No model requests and no desktop actions.
"""
from uuid import uuid4
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.computer_use_v2_action_session import (
    ComputerUseV2ActionSession, PreparedComputerUseV2Cycle,
)
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop

TARGET_IDS = {"IDC_ZAMAWIAJACY", "IDC_NEW", "IDC_FILTER", "IDC_EDYCJA", "IDC_SHOW_ALL"}
TARGET_LABELS = {
    "Wybierz istniejącego klienta", "Dodaj nowego klienta",
    "Filtr klientów", "Edytuj klienta", "Pokaż wszystkich klientów",
}


def main():
    print("=== CUSTOMER PICKER TRACE ===")
    ok, info = activate_windowhub_workflow_window()
    print("ACTIVATION =", ok)
    print("DETAILS =", info)
    if not ok:
        return 3

    scene = enrich_windowhub_scene(
        create_windows_desktop_agent_control_loop().observe_scene()
    )
    stage = stage_of(scene)
    print("STAGE =", stage)
    if stage != "document_properties":
        print("STOP: unexpected stage")
        return 4

    session = ComputerUseV2ActionSession()
    task_id = "trace-" + uuid4().hex[:12]
    prepared = session.prepare_cycle(
        scene, task_id=task_id, goal="Read only diagnostic",
        world_revision=1,
    )
    payload = prepared.request_payload
    entities = {e["ref"]: e for e in payload["world"]["entities"]}
    affordances = payload["world"]["affordances"]
    actions = payload["capabilities"]["actions"]
    print("SCENE_ELEMENTS =", len(scene.elements))
    print("MODEL_ENTITIES =", len(entities))
    print("MODEL_AFFORDANCES =", len(affordances))
    print("ACTIONS =", len(actions))

    found = 0
    for index, element in enumerate(scene.elements, 1):
        meta = element.metadata or {}
        auto_id = meta.get("automation_id")
        semantic = meta.get("semantic_label")
        if auto_id not in TARGET_IDS and semantic not in TARGET_LABELS:
            continue
        found += 1
        ref = f"ent_{index:04d}"
        current_actions = [a["name"] for a in actions if a.get("target_ref") == ref]
        current_affordances = [
            a["name"] for a in affordances if a.get("entity_ref") == ref
        ]
        # Do not expose original labels, values, runtime IDs or customer data.
        print(f"TARGET_{found}_ID =", auto_id if auto_id in TARGET_IDS else "OTHER")
        print(f"TARGET_{found}_POSITION =", index)
        print(f"TARGET_{found}_IN_WORLD =", ref in entities)
        print(f"TARGET_{found}_SEMANTIC =", semantic if semantic in TARGET_LABELS else "NONE")
        print(f"TARGET_{found}_CONTROL_KIND =", element.kind)
        print(f"TARGET_{found}_UIA_TYPE =", meta.get("uia_control_type"))
        print(f"TARGET_{found}_SOURCE =", meta.get("source"))
        print(f"TARGET_{found}_VISIBLE =", meta.get("uia_visible"))
        print(f"TARGET_{found}_ENABLED =", meta.get("uia_enabled"))
        print(f"TARGET_{found}_INTERACTION =", getattr(element.interaction_capability, "value", None))
        print(f"TARGET_{found}_NATIVE_ID_PRESENT =", bool(meta.get("uia_runtime_id")))
        print(f"TARGET_{found}_UNIQUE_UIA =", PreparedComputerUseV2Cycle._has_unique_uia_runtime_identity(scene, element))
        print(f"TARGET_{found}_AFFORDANCES =", current_affordances)
        print(f"TARGET_{found}_ACTIONS =", current_actions)
    print("CUSTOMER_TARGETS_IN_SCENE =", found)
    print("=== TRACE COMPLETE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
