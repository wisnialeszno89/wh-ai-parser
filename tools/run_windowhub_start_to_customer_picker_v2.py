"""Bounded Start1/offer document -> Document Properties -> customer picker workflow.

Only two strictly target-checked clicks are possible: NOWA OFERTA and the
existing-customer picker. Never selects customers, edits fields or saves.
"""
from pathlib import Path
import os
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.reasoning.navimind_task_reasoner_v2 import NaviMindTaskReasonerV2
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from tools.run_windowhub_customer_picker_once import main as picker_main


def main():
    print("=== WINDOWHUB START TO CUSTOMER PICKER ===")
    if any(os.environ.get(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("STOP: live authorization required")
        return 2
    ok, info = activate_windowhub_workflow_window()
    print("START_ACTIVATION =", ok, info)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    stage = stage_of(scene)
    print("INITIAL_STAGE =", stage)

    if stage in {"start", "offer_document"}:
        task_id = "start-" + uuid4().hex[:12]
        prepared = ComputerUseV2ActionSession().prepare_cycle(
            scene, task_id=task_id, session_id=task_id,
            goal="Kliknij tylko NOWA OFERTA, aby otworzyć formularz właściwości dokumentu.",
            world_revision=1, max_cycles=1,
        )
        entities = {e["ref"]: e for e in prepared.request_payload["world"]["entities"]}
        matches = [
            a for a in prepared.request_payload["capabilities"]["actions"]
            if a["name"].startswith("click_ent_")
            and entities.get(a.get("target_ref"), {}).get("label") == "NOWA OFERTA"
        ]
        print("START_TARGET_COUNT =", len(matches))
        if len(matches) != 1:
            print("STOP: NOWA OFERTA not uniquely available")
            return 4
        print("NOTICE: one NaviMind model request for opening new offer")
        reasoner = NaviMindTaskReasonerV2()
        response = reasoner.reason(prepared.request_payload)
        if response is None:
            print("STOP: NAVIMIND_ERROR =", reasoner.last_error)
            return 5
        print("START_DECISION =", response.get("decision"))
        print("START_CONFIDENCE =", response.get("confidence"))
        if (
            response.get("decision") != "act"
            or not isinstance(response.get("confidence"), (int, float))
            or response["confidence"] < 0.80
            or not isinstance(response.get("action"), dict)
            or response["action"].get("name") != matches[0]["name"]
            or response["action"].get("target_ref") != matches[0]["target_ref"]
        ):
            print("STOP: model did not select exact NOWA OFERTA capability")
            return 4
        try:
            resolved = prepared.resolve_action_decision(response)
            target = resolved.action.target
            if (
                resolved.action.name != "click_screen_element"
                or getattr(target, "label", None) != "NOWA OFERTA"
                or resolved.action.requires_confirmation
                or resolved.expected_postcondition.get("kind") != "scene_changed"
            ):
                raise ValueError("start_action_guard_failed")
            execute_v2_step(loop, scene, resolved)
        except (ValueError, KeyError, TypeError, RuntimeError) as exc:
            print("STOP: start execution guard:", str(exc))
            return 6
        print("START_ACTION_VERIFIED = True")
    elif stage != "document_properties":
        print("STOP: unexpected current stage; no action")
        return 4

    ok, info = activate_windowhub_workflow_window()
    print("PROPERTIES_ACTIVATION =", ok, info)
    if not ok:
        return 3
    current = enrich_windowhub_scene(loop.observe_scene())
    current_stage = stage_of(current)
    print("AFTER_START_STAGE =", current_stage)
    if current_stage != "document_properties":
        print("STOP: properties stage not confirmed; picker not attempted")
        return 4

    # Existing runner enforces the exact IDC_ZAMAWIAJACY local UIA identity
    # and the same one-action verified executor.
    result = picker_main()
    print("PICKER_EXIT_CODE =", result)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
