from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.agent_request import AgentRequest
from app.agent.runtime.windowhub_agent_runtime import (
    create_windowhub_agent_runtime,
)

from tools.inspect_live_windowhub_ui_targets import (
    _windowhub_hwnd,
    _window_title,
)
from tools.live_click_windowhub_target import _focus_window


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one or more natural-language requests through the "
            "same WindowHub AgentRuntime session."
        )
    )
    parser.add_argument(
        "--message",
        action="append",
        dest="messages",
        help=(
            "Natural-language task for the agent. Repeat --message to "
            "continue the same conversation/session."
        ),
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help=(
            "Optional explicit session id. When omitted, one id is "
            "generated for the whole command."
        ),
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="Seconds to wait after focusing WindowHub.",
    )
    return parser.parse_args()


def _print_plan(result) -> None:
    context = result.context
    plan = context.plan

    print()
    print("=== AGENT ===")
    print(
        f"intent={getattr(result.intent, 'value', result.intent)}"
    )
    print(f"executed={result.executed}")
    print(
        f"requires_manual_review={result.requires_manual_review}"
    )

    print()
    print("=== PLAN ===")
    if plan is None:
        print("plan=None")
    else:
        print(f"confidence={plan.confidence}")
        print(
            f"requires_manual_review="
            f"{plan.requires_manual_review}"
        )
        for step in plan.steps:
            action = step.action
            print(
                f"step[{step.index}] "
                f"name={action.name!r} "
                f"target={getattr(action, 'target', None)!r} "
                f"description={action.description!r}"
            )

    salesperson_questions = context.get_value(
        "salesperson_questions",
        (),
    )

    if salesperson_questions:
        print()
        print("=== SALESPERSON QUESTIONS ===")
        for question in salesperson_questions:
            print(f"- {question}")


def _print_execution(result) -> None:
    control = result.control_loop_result

    if control is None:
        print()
        print("=== CONTROL LOOP ===")
        print(
            "not executed: runtime stopped before GUI control "
            "because salesperson input is required."
        )
        return

    print()
    print("=== CONTROL LOOP ===")
    print(f"success={control.success}")
    print(
        "requires_manual_review="
        f"{control.requires_manual_review}"
    )
    print(f"stopped={control.stopped}")
    print(f"executed_actions={control.executed_actions}")
    print(f"failed_actions={control.failed_actions}")

    for index, execution in enumerate(
        control.execution_results,
        start=1,
    ):
        print()
        print(
            f"execution[{index}] "
            f"success={execution.success}"
        )

        attempt = execution.last_attempt
        if attempt is None:
            print("  attempt=None")
            continue

        execution_result = attempt.execution_result
        verification = attempt.verification_result

        print(
            "  execution_success="
            f"{getattr(execution_result, 'success', None)}"
        )
        print(
            "  execution_message="
            f"{getattr(execution_result, 'message', None)!r}"
        )
        print(
            "  execution_metadata="
            f"{getattr(execution_result, 'metadata', None)!r}"
        )
        print(
            "  verification_verified="
            f"{getattr(verification, 'verified', None)}"
        )
        print(
            "  verification_reason="
            f"{getattr(verification, 'reason', None)!r}"
        )


def main() -> int:
    args = parse_args()

    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print(
            "ABORTED: Set WH_REAL_WINDOWHUB=1 for explicit LIVE "
            "WindowHub execution."
        )
        return 2

    messages = args.messages or ["Otwórz nową ofertę"]
    session_id = args.session_id or f"live-{uuid4().hex}"

    hwnd = _windowhub_hwnd()
    if hwnd is None:
        print("ABORTED: No visible WindowHub main window was found.")
        return 3

    print(
        "Full AgentRuntime → WindowHub LIVE conversational smoke-test"
    )
    print(
        "============================================================="
    )
    print(f"windowhub_hwnd={hwnd}")
    print(f"windowhub_title={_window_title(hwnd)!r}")
    print(f"session_id={session_id!r}")
    print(f"turn_count={len(messages)}")

    if not _focus_window(hwnd):
        print(
            "ABORTED: WindowHub could not be made the foreground window."
        )
        return 4

    time.sleep(max(0.0, args.wait))

    runtime = create_windowhub_agent_runtime()

    final_result = None

    for turn_index, message in enumerate(
        messages,
        start=1,
    ):
        print()
        print("=" * 68)
        print(f"TURN {turn_index}/{len(messages)}")
        print("=" * 68)
        print(f"message={message!r}")

        request = AgentRequest(
            message=message,
            session_id=session_id,
        )

        result = runtime.run(request)
        final_result = result

        _print_plan(result)
        _print_execution(result)

    print()
    print("=== FINAL ===")

    if final_result is None:
        print("success=False")
        print("manual_review=True")
        print("stopped=True")
        return 6

    control = final_result.control_loop_result

    if control is None:
        print("success=False")
        print(
            "manual_review="
            f"{final_result.requires_manual_review}"
        )
        print("stopped=True")
        return 6

    print(f"success={control.success}")
    print(
        "manual_review="
        f"{control.requires_manual_review}"
    )
    print(f"stopped={control.stopped}")

    return 0 if control.success else 6


if __name__ == "__main__":
    raise SystemExit(main())
