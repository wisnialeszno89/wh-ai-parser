from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow direct execution via python tools/<script>.py from the repository root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.agent_request import AgentRequest
from app.agent.runtime.windows_desktop_agent_runtime import (
    create_windows_desktop_agent_runtime,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a semantic task through the generic Windows Universal Agent. "
            "Physical GUI execution is disabled unless COMPUTER_REAL=1."
        )
    )
    parser.add_argument(
        "--goal",
        required=True,
        help="The task to reason about and perform through the local safety path.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional stable session identifier for this task.",
    )
    args = parser.parse_args()

    runtime = create_windows_desktop_agent_runtime()
    live_mode = os.getenv("COMPUTER_REAL", "").strip() == "1"
    print("runtime: generic-windows-desktop")
    print("task_reasoner: configured")
    print("physical_execution_mode:", "LIVE" if live_mode else "DRY_RUN")

    result = runtime.run(
        AgentRequest(
            message=args.goal,
            session_id=args.session_id,
        )
    )

    plan = result.context.plan
    actions = (
        [step.action for step in plan.steps]
        if plan is not None
        else []
    )

    print("intent:", result.intent.value)
    print("runtime_executed:", result.executed)
    print("requires_manual_review:", result.requires_manual_review)
    print(
        "task_reasoning_failure:",
        result.context.get_value("task_reasoning_failure"),
    )
    print("planned_semantic_action_count:", len(actions))
    for index, action in enumerate(actions, start=1):
        print(f"action_{index}_name:", action.name)
        print(f"action_{index}_target:", action.target)
        print(f"action_{index}_requires_confirmation:", action.requires_confirmation)

    # Manual review is a safe, valid outcome; it is not reported as success.
    if result.requires_manual_review:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
