from __future__ import annotations

import sys
from pathlib import Path

# Allow direct execution via python tools/<script>.py from the repository root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.reasoning.navimind_task_reasoner import NaviMindTaskReasoner
from app.agent.reasoning.task_planning_context import TaskPlanningContext


def main() -> int:
    """Verify outbound authenticated NaviMind contract without computer I/O."""
    reasoner = NaviMindTaskReasoner()
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Synthetic smoke fixture",
                active_window_title="Synthetic smoke fixture",
            ),
            metadata={"synthetic_fixture": True},
        ),
        elements=(
            ScreenElement(
                kind="button",
                label="Synthetic Continue",
                confidence=0.99,
                interaction_capability=InteractionCapability.CLICKABLE,
            ),
        ),
    )
    context = TaskPlanningContext(
        request_message=(
            "This is a connectivity and contract smoke test only. "
            "Do not execute any computer action. Return a semantic proposal "
            "or request manual review if the contract cannot be satisfied."
        ),
        intent="computer_use",
        session_id="synthetic-navimind-smoke",
        capability_name="COMPUTER_USE",
        capability_description="Synthetic smoke-test capability only.",
        skill_name="SmokeTestSkill",
        scene=scene,
    )

    proposal = reasoner.reason(context)
    print("=" * 72)
    print("GENERIC WINDOWS -> NAVIMIND OUTBOUND SMOKE")
    print("=" * 72)
    print("endpoint_configured:", bool(reasoner.config.url))
    print("shared_secret_configured:", bool(reasoner.config.secret))
    print("transport_response_received:", proposal is not None)
    print("manual_review_requested:", proposal.requires_manual_review if proposal else None)
    print("semantic_action_count:", len(proposal.actions) if proposal else None)
    print("computer_action_executed: False")
    print("=" * 72)

    if proposal is None:
        print("Smoke failed: NaviMind did not return a valid contract response.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
