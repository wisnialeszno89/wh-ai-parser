"""One explicitly authorized, model-selected customer-picker click in WindowHub.

No creation, editing, saving or sending. A local AutomationId and semantic-label
guard must both agree before the standard verified executor is invoked.
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

EXPECTED_LABEL = "Wybierz istniejącego klienta"
EXPECTED_AUTOMATION_ID = "IDC_ZAMAWIAJACY"


def check_customer_picker_proposal(prepared, response):
    """Resolve and approve only this particular UIA control, fail closed otherwise."""
    if not isinstance(response, dict) or response.get("decision") != "act":
        raise ValueError("model_did_not_select_action")
    if response.get("confidence", 0) < 0.80:
        raise ValueError("model_confidence_too_low")
    resolved = prepared.resolve_action_decision(response)
    action = resolved.action
    target = action.target
    if action.name != "click_screen_element":
        raise ValueError("not_a_click_action")
    if getattr(target, "automation_id", None) != EXPECTED_AUTOMATION_ID:
        raise ValueError("unexpected_automation_id")
    if resolved.expected_postcondition.get("kind") != "scene_changed":
        raise ValueError("scene_change_required")
    if action.requires_confirmation:
        raise ValueError("unexpected_confirmation_required")
    original = prepared.snapshot.reference_map.resolve(
        resolved.target_ref,
        task_id=prepared.task_id,
        world_revision=prepared.world_revision,
    )
    meta = original.metadata or {}
    if (meta.get("semantic_label") != EXPECTED_LABEL
        or meta.get("automation_id") != EXPECTED_AUTOMATION_ID
        or meta.get("uia_enabled") is not True
        or meta.get("uia_visible") is not True):
        raise ValueError("customer_picker_identity_not_verified")
    return resolved


def main():
    print("=== NAVIMIND CUSTOMER PICKER LIVE ===")
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        print("STOP: explicit live authorization required")
        return 2
    ok, info = activate_windowhub_workflow_window()
    print("ACTIVATION =", ok)
    print("DETAILS =", info)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    print("BEFORE_STAGE =", stage_of(scene))
    if stage_of(scene) != "document_properties":
        print("STOP: not at document properties")
        return 4

    session = ComputerUseV2ActionSession()
    task_id = "customer-" + uuid4().hex[:12]
    prepared = session.prepare_cycle(
        scene,
        task_id=task_id,
        session_id=task_id,
        goal="Otwórz wyłącznie wybór istniejącego klienta. Nie wybieraj klienta, nie zapisuj ani nie wysyłaj danych.",
        world_revision=1,
        max_cycles=1,
    )
    entries = prepared.request_payload["capabilities"]["actions"]
    entities = {e["ref"]: e for e in prepared.request_payload["world"]["entities"]}
    picker = [
        a for a in entries
        if a["name"].startswith("click_ent_")
        and entities.get(a.get("target_ref"), {}).get("label") == EXPECTED_LABEL
    ]
    print("MATCHING_PICKER_CAPABILITIES =", len(picker))
    if len(picker) != 1:
        print("STOP: customer picker not uniquely offered to the model")
        return 4

    print("NOTICE: semantic UI description and goal sent to configured NaviMind")
    reasoner = NaviMindTaskReasonerV2()
    response = reasoner.reason(prepared.request_payload)
    if response is None:
        print("STOP: NAVIMIND_ERROR =", reasoner.last_error)
        return 5
    print("MODEL_DECISION =", response.get("decision"))
    print("MODEL_CONFIDENCE =", response.get("confidence"))
    if response.get("decision") != "act":
        print("STOP: model declined to act")
        return 4
    try:
        resolved = check_customer_picker_proposal(prepared, response)
    except (ValueError, KeyError, TypeError) as exc:
        print("STOP: customer picker guard:", str(exc))
        return 6
    print("APPROVED_TARGET =", EXPECTED_LABEL)
    print("APPROVED_AUTOMATION_ID =", EXPECTED_AUTOMATION_ID)
    try:
        execute_v2_step(loop, scene, resolved, approved_persistent=False)
    except (ValueError, RuntimeError) as exc:
        print("STOP: local execution/verification:", str(exc))
        return 6
    print("ACTION_VERIFIED = click_screen_element")
    after = enrich_windowhub_scene(loop.observe_scene())
    print("AFTER_STAGE =", stage_of(after) or "unmapped")
    print("STOP: one-action limit reached; no customer was selected or saved by this workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
