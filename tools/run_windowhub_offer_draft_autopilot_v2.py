"""WindowHub offer-creation autopilot, bounded to an unsaved working draft.

Activates WindowHub automatically; observes after each step; stops at a
position wizard or at a verifiable blocker. Never commits, saves or sends.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
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

# The labels below are the only customer-neutral navigation controls approved
# for this workflow. Selecting a customer requires a separate exact identifier.
NAVIGATION = {
    "start": {"NOWA OFERTA"},
    "offer_document": {"NOWA OFERTA"},
    "document_properties": {"Wybierz istniejącego klienta"},
}
TARGET_STAGES = {"position", "dimensions", "basic_parameters", "glazing", "hardware"}
MAX_ACTIONS = 12


def permitted_label(stage, label, *, customer):
    if stage in NAVIGATION:
        return label in NAVIGATION[stage]
    # Exact match to a specifically requested customer only; do not infer from
    # similar surnames or blindly select rows in a customer database.
    if stage in {"windowhub_unmapped", "customer_lookup"}:
        return bool(customer) and label == customer
    return False


def pick_action(prepared, response, stage, *, customer):
    if response.get("decision") != "act":
        raise ValueError("no_executable_decision")
    confidence = response.get("confidence")
    if type(confidence) not in (int, float) or confidence < .80:
        raise ValueError("confidence_below_threshold")
    raw = response.get("action")
    if not isinstance(raw, dict):
        raise ValueError("action_missing")
    action_name = raw.get("name")
    capabilities = {
        c["name"]: c for c in prepared.request_payload["capabilities"]["actions"]
    }
    cap = capabilities.get(action_name)
    if not cap or not action_name.startswith("click_ent_"):
        raise ValueError("not_an_allowlisted_click")
    if cap["target_ref"] != raw.get("target_ref"):
        raise ValueError("reference_mismatch")
    entities = {e["ref"]: e for e in prepared.request_payload["world"]["entities"]}
    label = entities.get(cap["target_ref"], {}).get("label")
    if not isinstance(label, str) or not permitted_label(stage, label, customer=customer):
        raise ValueError("action_not_allowed_in_stage")
    if cap.get("requires_confirmation") or raw.get("requires_confirmation"):
        raise ValueError("confirmation_or_persistence_not_allowed")
    resolved = prepared.resolve_action_decision(response)
    if resolved.action.name != "click_screen_element":
        raise ValueError("unexpected_action_kind")
    if resolved.action.requires_confirmation:
        raise ValueError("confirmation_not_allowed")
    if resolved.expected_postcondition.get("kind") != "scene_changed":
        raise ValueError("scene_change_verification_required")
    return resolved, label



def resolve_verified_navigation(prepared, capability):
    """Locally select one approved capability; still validate full V2 contract.

    This is a deterministic WindowHub navigation policy, not an AI decision.
    It uses the same scoped reference map and executor as model actions.
    """
    if capability.get("requires_confirmation") is not False:
        raise ValueError("navigation_requires_confirmation")
    request = prepared.request_payload
    response = {
        "version": "2",
        "task_id": request["task_id"],
        "decision": "act",
        "rationale": "Locally validated unique WindowHub navigation control.",
        "confidence": 1.0,
        "observation_request": None,
        "action": {
            "name": capability["name"],
            "target_ref": capability["target_ref"],
            "value": None,
            "expected_postcondition": {"kind": "scene_changed"},
            "requires_confirmation": False,
        },
        "completion": None,
        "requires_manual_review": False,
    }
    return prepared.resolve_action_decision(response)

def main(argv=None):
    parser = argparse.ArgumentParser(description="WindowHub offer draft navigation")
    parser.add_argument("--customer", default="", help="Exact existing test customer label; optional")
    parser.add_argument("--max-actions", type=int, default=8)
    args = parser.parse_args(argv)
    if not 1 <= args.max_actions <= MAX_ACTIONS:
        parser.error("--max-actions must be between 1 and 12")
    if len(args.customer) > 150:
        parser.error("customer identifier is too long")
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        print("STOP = explicit live authorization required")
        return 2

    print("=== WINDOWHUB AUTONOMOUS OFFER DRAFT ===")
    print("CUSTOMER_SPECIFIED =", bool(args.customer))
    ok, _ = activate_windowhub_workflow_window()
    print("AUTO_ACTIVATION =", ok)
    if not ok:
        print("STOP = no safe foreground WindowHub")
        return 3

    loop = create_windows_desktop_agent_control_loop()
    reasoner = None  # construct only if an unfamiliar customer-selection screen appears
    session = ComputerUseV2ActionSession()
    task_id = "offer-" + uuid4().hex[:12]
    for step in range(args.max_actions):
        scene = enrich_windowhub_scene(loop.observe_scene())
        stage = stage_of(scene)
        print(f"STEP_{step + 1}_STAGE =", stage, flush=True)
        if stage in TARGET_STAGES:
            print("RESULT = OFFER_POSITION_EDITOR_REACHED")
            print("FINAL_SAVE = NOT_AUTHORIZED")
            return 0
        if stage is None:
            print("STOP = WindowHub lost foreground; no input")
            return 4
        if stage == "document_properties" and not args.customer:
            print("STOP = CUSTOMER_NEEDED_FOR_NEXT_STEP")
            print("RESULT = DOCUMENT_PROPERTIES_REACHED")
            return 4

        # Construct fresh capabilities once per scene revision.
        prepared = session.prepare_cycle(
            scene,
            task_id=task_id,
            session_id=task_id,
            goal=(
                "Rozpocznij nowa oferte robocza i przejdz do kreatora pozycji "
                "okiennej. Nie zapisuj, nie wysylaj, nie zatwierdzaj dokumentu. "
                "Na tym etapie wybierz tylko dozwolona nawigacje. "
                + ("Wybierz wylacznie dokladnie wskazanego klienta: " + args.customer
                   if args.customer else "Nie wybieraj klienta bez identyfikatora.")
            ),
            world_revision=step + 1,
            cycle=step,
            max_cycles=args.max_actions,
        )
        entities = {e["ref"]: e for e in prepared.request_payload["world"]["entities"]}
        allowed = [
            a for a in prepared.request_payload["capabilities"]["actions"]
            if a["name"].startswith("click_ent_")
            and permitted_label(
                stage,
                entities.get(a["target_ref"], {}).get("label"),
                customer=args.customer,
            )
        ]
        print(f"STEP_{step + 1}_ALLOWED_ACTIONS =", len(allowed))
        if len(allowed) != 1:
            print("STOP = expected one unique safe navigation action")
            return 4

        if stage in NAVIGATION:
            # Deterministic, already-known navigation is a local operation.
            # No model call for NOWA OFERTA or opening the customer picker.
            try:
                resolved = resolve_verified_navigation(prepared, allowed[0])
                label = entities[allowed[0]["target_ref"]]["label"]
            except (KeyError, TypeError, ValueError) as exc:
                print("STOP = LOCAL_NAVIGATION_POLICY", str(exc))
                return 5
            print(f"STEP_{step + 1}_PLANNER = LOCAL_VERIFIED")
        else:
            # Unknown screens require AI and an exact customer label. Do not
            # infer a customer from similar text or arbitrary database rows.
            if reasoner is None:
                reasoner = NaviMindTaskReasonerV2()
            response = reasoner.reason(prepared.request_payload)
            if response is None:
                print("STOP = NAVIMIND_ERROR", reasoner.last_error)
                return 5
            print(f"STEP_{step + 1}_MODEL_DECISION =", response.get("decision"))
            try:
                resolved, label = pick_action(
                    prepared, response, stage, customer=args.customer
                )
                if response["action"]["name"] != allowed[0]["name"]:
                    raise ValueError("not_the_unique_allowed_action")
            except (KeyError, TypeError, ValueError) as exc:
                print("STOP = MODEL_OR_POLICY", str(exc))
                return 5
        print(f"STEP_{step + 1}_ACTION =", label if label != args.customer else "EXACT_CUSTOMER_MATCH")
        try:
            execute_v2_step(loop, scene, resolved, approved_persistent=False)
        except (RuntimeError, ValueError) as exc:
            # An action might have physically happened even when verification
            # fails. Never retry it blindly; inspect the live UI separately.
            print("STOP = EXECUTION_NOT_VERIFIED", str(exc))
            print("NO_AUTOMATIC_RETRY = True")
            return 6
        print(f"STEP_{step + 1}_VERIFIED = True")

    scene = enrich_windowhub_scene(loop.observe_scene())
    stage = stage_of(scene)
    print("FINAL_STAGE =", stage)
    if stage in TARGET_STAGES:
        print("RESULT = OFFER_POSITION_EDITOR_REACHED")
        return 0
    print("STOP = action budget exhausted")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
