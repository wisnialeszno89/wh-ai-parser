"""WH Okna live acceptance: exactly one verified 'Dodaj' action on OFR.

Operator prepares a disposable test offer in WindowHub and explicitly opts in.
The existing V2 coordinator performs scope enforcement, input and postcondition
verification. No focus switching, no accept/save/send and no ZLC order access.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.agent_action import AgentAction
from app.agent.knowledge.whokna_live_offer_gate import observe_offer_gate
from app.agent.knowledge.whokna_offer_guide import load_reference, offer_plan
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.runtime.active_document_scope import (
    unique_active_document_control, duplicate_document_action_status,
)
from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step
from app.agent.runtime.windowhub_mdi_native_probe import (
    enrich_native_mdi_document_scope, inspect_native_mdi_button_ancestry,
    diagnose_native_scope_enrichment,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def diagnose_add_scope(scene) -> dict:
    """Structured read-only reason why native document ownership is unresolved."""
    selected = duplicate_document_action_status(scene, label="Dodaj")
    try:
        enriched = enrich_native_mdi_document_scope(scene)
        scoped = duplicate_document_action_status(enriched, label="Dodaj")
        scoped["safe_unique_active_target"] = (
            enriched is not scene and unique_active_document_control(enriched, label="Dodaj") is not None
        )
    except Exception as exc:
        scoped = {"diagnostic_error": type(exc).__name__}
    try:
        native = inspect_native_mdi_button_ancestry(scene)
    except Exception as exc:
        native = {"status": "diagnostic_error_" + type(exc).__name__}
    try:
        precise = diagnose_native_scope_enrichment(scene)
    except Exception as exc:
        # Diagnostic failure must not change the action gate or authorize
        # any click; preserve a stable error category for offline fixtures.
        precise = {"status": "diagnostic_error_" + type(exc).__name__}
    return {
        "enrichment": precise,
        "selected_tab_status": selected["selected_document_status"],
        "observed_dodaj": selected["observed"],
        "native_probe_status": native.get("status"),
        "native_uia_matched": native.get("uia_matched_uniquely"),
        "native_exact_mdi_ancestors": native.get("with_exact_mdi_ancestor"),
        "native_without_mdi_ancestor": native.get("with_no_mdi_ancestor"),
        "native_ambiguous_ancestors": native.get("with_ambiguous_mdi_ancestor"),
        "active_scope_proven": scoped.get("active_scope_proven", 0),
        "scope_unresolved": scoped.get("unresolved_scope", 0),
        "safe_unique_target": scoped.get("safe_unique_active_target", False),
    }


def stopped_foreground_diagnostic(gate, scene) -> dict:
    """Non-sensitive foreground diagnostic; no window captions or values."""
    application = (
        scene.observation.state.active_application or ""
    ).replace("\\\\", "/").rsplit("/", 1)[-1].casefold()
    rectangle = scene.observation.metadata.get("window_rect")
    if isinstance(rectangle, (list, tuple)) and len(rectangle) == 4:
        rect_type = "four_coordinates"
    elif rectangle is None:
        rect_type = "missing"
    else:
        rect_type = type(rectangle).__name__
    return {
        "gate_reason": gate.reason,
        "scene_stage": gate.scene_stage,
        "is_windowhub_process": application == "okna.exe",
        "foreground_title_kind": (
            "offer" if gate.scene_stage == "offer_document"
            else "wizard" if gate.scene_stage == "wizard"
            else "start" if gate.scene_stage == "start"
            else "other_or_unrecognized"
        ),
        "window_rect_type": rect_type,
        "scene_elements": len(scene.elements),
    }


def prepare_add_action(scene):
    """Only a uniquely scoped semantic UIA control can be executed."""
    gate = scene.observation.state
    title = (gate.active_window_title or "").strip()
    if not title.casefold().startswith("okna - ofr/"):
        raise ValueError("test_offer_document_required")
    native_scene = enrich_native_mdi_document_scope(scene)
    if native_scene is scene:
        raise ValueError("unique_active_dodaj_not_verified")
    element = unique_active_document_control(native_scene, label="Dodaj")
    if element is None:
        raise ValueError("unique_active_dodaj_not_verified")
    meta = element.metadata or {}
    runtime_id = meta.get("uia_runtime_id")
    automation_id = meta.get("automation_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip():
        raise ValueError("verified_dodaj_runtime_id_missing")
    if not isinstance(automation_id, str) or not automation_id.strip():
        raise ValueError("verified_dodaj_automation_id_missing")
    action = AgentAction(
        name="click_screen_element",
        description="Open one new position in the verified test offer",
        target=SemanticTargetQuery(
            role="button", label="Dodaj", automation_id=automation_id,
            uia_runtime_id=runtime_id,
        ),
        requires_environment_observation=True,
    )
    return native_scene, SimpleNamespace(
        action=action,
        target_ref="verified_dodaj",
        expected_postcondition={"kind": "scene_changed"},
    ), title[7:]


def main():
    parser = argparse.ArgumentParser(description="One bounded WindowHub offer action")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--offer", help="Exact caption of the disposable test OFR")
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--start-delay", type=int, default=15)
    args = parser.parse_args()
    if os.name != "nt":
        print("WH_STEP_STOP=windows_required")
        return 2
    if not 0 <= args.start_delay <= 30:
        print("WH_STEP_STOP=invalid_delay")
        return 2
    if args.execute_live and not (args.offer or "").startswith("OFR/"):
        print("WH_STEP_STOP=explicit_test_offer_required")
        return 2
    if args.execute_live and not (
        os.environ.get("COMPUTER_USE_LIVE") == "1"
        and os.environ.get("WH_REAL_WINDOWHUB") == "1"
    ):
        print("WH_STEP_STOP=live_environment_authorization_missing")
        return 2
    try:
        plan = offer_plan(
            load_reference(), width=args.width, height=args.height,
            quantity=args.quantity,
        )
    except (ValueError, OSError, KeyError) as exc:
        print("WH_STEP_STOP=invalid_guided_offer_specification")
        return 2
    if plan["stages"][1]["id"] != "position" or (
        plan["safety"]["forbid_zlc_order_mutation"] is not True
    ):
        print("WH_STEP_STOP=guided_plan_not_safe")
        return 2
    print("WH_STEP_GUIDE_STAGE=position", flush=True)
    print("WH_STEP_FOCUS_MODE=MANUAL_SAFE", flush=True)
    print("WH_STEP_PREPARE=Show disposable OFR offer in WindowHub", flush=True)
    time.sleep(args.start_delay)
    loop = create_windows_desktop_agent_control_loop()
    observed, scene = observe_offer_gate(loop)
    if not observed.ok or observed.scene_stage != "offer_document":
        import json
        print("WH_STEP_FOREGROUND_DIAGNOSTICS=" + json.dumps(
            stopped_foreground_diagnostic(observed, scene), ensure_ascii=False,
        ), flush=True)
        print("WH_STEP_STOP=not_verified_offer_document", flush=True)
        print("WH_STEP_ACTIONS_EXECUTED=0", flush=True)
        return 4
    if args.offer is not None and (
        scene.observation.state.active_window_title or ""
    ).strip() != "Okna - " + args.offer:
        print("WH_STEP_STOP=test_offer_mismatch", flush=True)
        print("WH_STEP_ACTIONS_EXECUTED=0", flush=True)
        return 4
    try:
        native_scene, resolved, offer_name = prepare_add_action(scene)
    except (ValueError, RuntimeError, OSError) as exc:
        if str(exc) == "unique_active_dodaj_not_verified":
            import json
            diagnosis = diagnose_add_scope(scene)
            print("WH_STEP_SCOPE_DIAGNOSTICS=" + json.dumps(diagnosis, ensure_ascii=False), flush=True)
        print("WH_STEP_STOP=" + str(exc), flush=True)
        print("WH_STEP_ACTIONS_EXECUTED=0", flush=True)
        return 4
    print("WH_STEP_TARGET=verified_active_document_Dodaj", flush=True)
    if not args.execute_live:
        import json
        print("WH_STEP_SCOPE_DIAGNOSTICS=" + json.dumps(
            diagnose_add_scope(scene), ensure_ascii=False,
        ), flush=True)
        print("WH_STEP_MODE=PREFLIGHT_ONLY", flush=True)
        print("WH_STEP_ACTIONS_EXECUTED=0", flush=True)
        return 0
    print("WH_STEP_MODE=ONE_VERIFIED_LIVE_ACTION", flush=True)
    try:
        execute_v2_step(
            loop, native_scene, resolved,
            expected_offer=args.offer or offer_name,
            approved_persistent=False,
        )
    except (RuntimeError, ValueError) as exc:
        print("WH_STEP_STOP=" + type(exc).__name__ + ": " + str(exc), flush=True)
        return 5
    print("WH_STEP_POSTCONDITION=verified_new_position_wizard", flush=True)
    print("WH_STEP_ACTIONS_EXECUTED=1", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
