"""One strictly bounded local WindowHub Add-position action (NO model, NO Vercel).

Default dry-run. Real GUI input requires --execute-live, two environment flags,
a unique MDI-scoped native button, an exact active offer identity and a fresh
local policy check. Never creates a new offer or saves any document.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_mdi_native_probe import enrich_native_mdi_document_scope
from app.agent.runtime.active_document_scope import unique_active_document_control
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.runtime.windowhub_goal_v2_coordinator import (
    enforce_v2_live_policy, verified_v2_outcome, execute_v2_step,
)


def run(expected_offer: str, execute_live: bool = False) -> int:
    if os.name != "nt":
        print("STOP=windows_only")
        return 2
    if not expected_offer.startswith("OFR/") or len(expected_offer) > 36:
        print("STOP=invalid_expected_offer")
        return 2

    # Foreground transfer only; activation never creates a new offer.
    focused, info = activate_windowhub_workflow_window()
    print("WINDOWHUB_ACTIVATION=" + info)
    if not focused:
        print("STOP=windowhub_not_found")
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(enrich_native_mdi_document_scope(loop.observe_scene()))
    title = (scene.observation.state.active_window_title or "").strip()
    if title.casefold() != ("Okna - " + expected_offer).casefold():
        print("STOP=active_offer_mismatch")
        return 4
    if stage_of(scene) != "offer_document":
        print("STOP=not_offer_document")
        return 4

    button = unique_active_document_control(scene, label="Dodaj")
    if button is None:
        print("STOP=ambiguous_or_unscoped_add_button")
        return 4

    task_id = "local-wh-" + uuid4().hex[:16]
    prepared = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id=task_id, session_id=task_id,
        goal="Dodaj nowa pozycje okienna do aktywnej oferty",
        world_revision=1, cycle=0, max_cycles=1,
        knowledge=None, experience=(),
        observed_at=datetime.now(timezone.utc).isoformat(),
    )
    ref_map = prepared.snapshot.reference_map
    matched = []
    for cap in prepared.request_payload["capabilities"]["actions"]:
        if not cap["name"].startswith("click_ent_"):
            continue
        try:
            element = ref_map.resolve(cap["target_ref"], task_id=task_id, world_revision=1)
        except (ValueError, KeyError, TypeError):
            continue
        if element is button:
            matched.append(cap)
    if len(matched) != 1:
        print("STOP=unique_add_capability_not_found")
        return 4
    cap = matched[0]
    decision = {
        "version": "2",
        "task_id": task_id,
        "decision": "act",
        "rationale": "Explicitly scoped single local Add-position capability.",
        "confidence": 1.0,
        "observation_request": None,
        "action": {
            "name": cap["name"],
            "target_ref": cap["target_ref"],
            "value": None,
            "expected_postcondition": {"kind": "scene_changed"},
            "requires_confirmation": cap["requires_confirmation"],
        },
        "completion": None,
        "requires_manual_review": False,
    }
    try:
        resolved = prepared.resolve_action_decision(decision)
        enforce_v2_live_policy(scene, resolved)
        expected = verified_v2_outcome(resolved, baseline_scene=scene)
    except (ValueError, KeyError, RuntimeError) as exc:
        print("STOP=local_policy_rejected:" + type(exc).__name__)
        return 4
    if expected.expected_window_title != "Dodawanie nowej pozycji":
        print("STOP=missing_specific_wizard_postcondition")
        return 4

    print("LOCAL_ADD_TARGET=UNIQUE_MDI_SCOPED")
    print("EXPECTED_OFFER=" + expected_offer)
    print("EXPECTED_POSTCONDITION=Dodawanie nowej pozycji")
    if not execute_live:
        print("DRY_RUN_PASS=True")
        print("INPUT_EXECUTED=False")
        return 0

    if os.getenv("WH_REAL_WINDOWHUB") != "1" or os.getenv("COMPUTER_USE_LIVE") != "1":
        print("STOP=missing_explicit_live_flags")
        return 2
    try:
        execute_v2_step(loop, scene, resolved)
    except (ValueError, RuntimeError) as exc:
        print("LOCAL_ADD_RESULT=NOT_VERIFIED")
        print("LOCAL_ADD_ERROR=" + type(exc).__name__)
        return 5
    print("LOCAL_ADD_RESULT=VERIFIED")
    print("LOCAL_ADD_ACTIONS_EXECUTED=1")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="One guarded Add-position action on active WindowHub offer")
    parser.add_argument("--offer", required=True, help="Exact offer ID, e.g. OFR/4687-")
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    return run(args.offer, execute_live=args.execute_live)


if __name__ == "__main__":
    raise SystemExit(main())
