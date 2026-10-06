from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.agent.learning.learned_workflow_replayer import (
    LearnedWorkflowReplayer,
)
from app.agent.runtime.windowhub_agent_control_loop import (
    create_windowhub_agent_control_loop,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Replay a learned WindowHub workflow through the Universal "
            "Agent control loop."
        )
    )
    parser.add_argument(
        "--workflow",
        default="outputs/learned_windowhub_workflow.json",
        help="Path to the learned workflow JSON.",
    )
    parser.add_argument(
        "--message",
        default=None,
        help="Optional user message used as the replay request.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Enable real mouse execution. Without this flag the robot "
            "runs in DRY_RUN mode."
        ),
    )
    args = parser.parse_args()

    workflow_path = Path(args.workflow)

    try:
        workflow = LearnedWorkflowReplayer.load_json(
            workflow_path
        )
    except Exception as exc:
        print(f"[REPLAY ERROR] Could not load workflow: {exc}")
        return 1

    if workflow.application and (
        workflow.application.casefold() != "windowhub"
    ):
        print(
            "[REPLAY ERROR] This WindowHub replay tool only accepts "
            f"WindowHub workflows, got {workflow.application!r}."
        )
        return 1

    if args.live:
        os.environ["WH_REAL_WINDOWHUB"] = "1"
    else:
        os.environ.pop("WH_REAL_WINDOWHUB", None)

    print("=" * 100)
    print("WINDOWHUB — REPLAY WYUCZONEGO WORKFLOW")
    print("=" * 100)
    print(f"Workflow : {workflow.name}")
    print(f"Trigger  : {workflow.trigger}")
    print(f"Kroki    : {len(workflow.steps)}")
    print(
        "Tryb     : "
        + ("LIVE" if args.live else "DRY_RUN")
    )
    print()

    try:
        result = LearnedWorkflowReplayer(
            control_loop=create_windowhub_agent_control_loop()
        ).replay(
            workflow,
            request_message=args.message,
        )
    except Exception as exc:
        print(f"[REPLAY ERROR] {exc}")
        return 1

    print(
        f"RESULT   : {'SUCCESS' if result.success else 'FAILED'}"
    )
    print(
        f"Postęp   : {result.completed_steps}/{result.total_steps}"
    )

    for step_result in result.control_loop_result.step_results:
        status = getattr(
            getattr(step_result, "status", None),
            "value",
            str(getattr(step_result, "status", "?")),
        )
        reason = getattr(
            step_result,
            "reason",
            "",
        )
        print(
            f"  STEP {step_result.action_name}: "
            f"{status}"
            + (f" — {reason}" if reason else "")
        )

    print("=" * 100)
    return 0 if result.success else 2


if __name__ == "__main__":
    raise SystemExit(main())
