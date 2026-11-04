"""Offline Observe -> V2 contract -> proposed semantic action -> local verification.

This uses a synthetic V2 reply. It is NOT an LLM reasoning test, a live
WindowHub test, or proof of a deployed NaviMind server. Never sends network
traffic and never controls the desktop.
"""
from __future__ import annotations

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.runtime.windowhub_goal_v2_coordinator import (
    enforce_v2_live_policy, verified_v2_outcome,
)
from app.agent.verification.outcome_verifier import OutcomeVerifier


def synthetic_scene(title: str, *, native_id="NOWA_OFERTA", label="NOWA OFERTA") -> ScreenScene:
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title=title,
                screen_width=1400,
                screen_height=900,
            ),
        ),
        elements=(
            ScreenElement(
                kind="button",
                label=label,
                x=20, y=20, width=150, height=40,
                confidence=0.99,
                interaction_capability=InteractionCapability.CLICKABLE,
                metadata={
                    "source": "windows_ui_automation",
                    "uia_control_type": "button",
                    "uia_enabled": True,
                    "uia_visible": True,
                    "uia_runtime_id": "[synthetic-windowhub-start]",
                    "automation_id": native_id,
                },
            ),
        ),
    )


def synthetic_reply(prepared, action):
    return {
        "version": "2",
        "task_id": prepared.request_payload["task_id"],
        "decision": "act",
        "rationale": "Synthetic protocol fixture for offline validation, not model reasoning.",
        "confidence": 0.99,
        "observation_request": None,
        "action": {
            "name": action["name"],
            "target_ref": action["target_ref"],
            "value": None,
            "expected_postcondition": {"kind": "scene_changed"},
            "requires_confirmation": action["requires_confirmation"],
        },
        "completion": None,
        "requires_manual_review": False,
    }


def evaluate_offline_v2_roundtrip() -> dict[str, object]:
    scene = enrich_windowhub_scene(synthetic_scene("Okna - Start1"))
    prepared = ComputerUseV2ActionSession().prepare_cycle(
        scene,
        task_id="offline-windowhub-protocol-test",
        session_id="offline-windowhub-protocol-test",
        goal="Otwórz nową ofertę",
        world_revision=1,
        observed_at="2026-11-04T12:00:00Z",
    )
    matching = [
        action for action in prepared.request_payload["capabilities"]["actions"]
        if action["name"].startswith("click_ent_")
        and action["target_ref"] is not None
    ]
    if len(matching) != 1:
        raise AssertionError("synthetic_new_offer_capability_not_unique")
    resolved = prepared.resolve_action_decision(synthetic_reply(prepared, matching[0]))
    enforce_v2_live_policy(scene, resolved)
    expected = verified_v2_outcome(resolved, baseline_scene=scene)
    unchanged = OutcomeVerifier().verify(expected, scene)
    changed = OutcomeVerifier().verify(
        expected, synthetic_scene("Właściwości dokumentu"),
    )
    if unchanged.verified is not False or changed.verified is not True:
        raise AssertionError("v2_navigation_postcondition_incorrect")
    return {
        "request_version": prepared.request_payload["version"],
        "capabilities": len(prepared.request_payload["capabilities"]["actions"]),
        "proposed_action": resolved.action.name,
        "native_selector_stayed_local": (
            "[synthetic-windowhub-start]" not in str(prepared.request_payload)
            and "NOWA_OFERTA" not in str(prepared.request_payload)
        ),
        "unchanged_rejected": unchanged.verified is False,
        "changed_accepted": changed.verified is True,
    }


def main() -> int:
    result = evaluate_offline_v2_roundtrip()
    for key, value in result.items():
        print(f"OFFLINE_V2_{key.upper()}={value}")
    print("OFFLINE_V2_STATUS=PASS")
    print("MODE=synthetic only; no NaviMind HTTP call and no mouse/keyboard input")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
