from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

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


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a configurable WindowHub offer smoke-test. "
            "The same semantic request is sent through one session so "
            "the agent replans against the fresh GUI scene after each step."
        )
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=12,
        help="Maximum number of agent turns.",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=0.8,
        help="Seconds to wait after focusing WindowHub.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Optional explicit session id.",
    )
    return parser.parse_args()


def _scenario_message() -> str:
    return (
        "Przygotuj nową ofertę w WindowHub. "
        f"Klient: {_env('AGENT_SMOKE_CUSTOMER', 'Test Client')}. "
        f"Produkt: {_env('AGENT_SMOKE_PRODUCT', 'okno')}. "
        f"Ilość: {_env('AGENT_SMOKE_QUANTITY', '1')}. "
        f"Wymiary: {_env('AGENT_SMOKE_WIDTH', '1230')} x "
        f"{_env('AGENT_SMOKE_HEIGHT', '1480')} mm. "
        f"Otwarcie: {_env('AGENT_SMOKE_OPENING', 'FIX')}. "
        f"Kolor: {_env('AGENT_SMOKE_COLOR', 'Biały')}."
    )


def _print_result(turn: int, result) -> None:
    print()
    print("=" * 72)
    print(f"TURN {turn}")
    print("=" * 72)

    print("=== AGENT ===")
    print(
        f"intent={getattr(result.intent, 'value', result.intent)}"
    )
    print(f"executed={result.executed}")
    print(
        f"requires_manual_review={result.requires_manual_review}"
    )

    plan = result.context.plan
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
                f"value={getattr(action, 'value', None)!r} "
                f"description={action.description!r}"
            )

    control = result.control_loop_result
    print()
    print("=== CONTROL LOOP ===")
    if control is None:
        print(
            "not executed: runtime stopped before GUI control."
        )
        return

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
            f"execution[{index}] success={execution.success}"
        )

        attempt = execution.last_attempt
        if attempt is None:
            print("  attempt=None")
            continue

        execution_result = attempt.execution_result
        verification = attempt.verification_result

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
    load_dotenv()

    args = parse_args()

    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print(
            "ABORTED: Set WH_REAL_WINDOWHUB=1 for explicit LIVE "
            "WindowHub execution."
        )
        return 2

    if os.environ.get("AGENT_TASK_REASONING") != "1":
        print(
            "ABORTED: Set AGENT_TASK_REASONING=1 to use the "
            "OpenAI task reasoner."
        )
        return 2

    hwnd = _windowhub_hwnd()
    if hwnd is None:
        print("ABORTED: No visible WindowHub main window was found.")
        return 3

    if not _focus_window(hwnd):
        print(
            "ABORTED: WindowHub could not be made the foreground window."
        )
        return 4

    time.sleep(max(0.0, args.wait))

    session_id = args.session_id or f"offer-smoke-{uuid4().hex}"
    message = _scenario_message()
    runtime = create_windowhub_agent_runtime()

    print("WindowHub configurable offer smoke-test")
    print("=======================================")
    print(f"windowhub_hwnd={hwnd}")
    print(f"windowhub_title={_window_title(hwnd)!r}")
    print(f"session_id={session_id!r}")
    print(f"turn_limit={args.turns}")
    print(f"scenario={message}")

    final_result = None

    for turn in range(1, max(1, args.turns) + 1):
        result = runtime.run(
            AgentRequest(
                message=message,
                session_id=session_id,
            )
        )
        final_result = result

        _print_result(turn, result)

        control = result.control_loop_result
        if (
            control is None
            or control.requires_manual_review
            or control.stopped
            or not control.success
        ):
            break

    print()
    print("=== FINAL ===")

    if final_result is None:
        print("success=False")
        return 6

    control = final_result.control_loop_result
    if control is None:
        print("success=False")
        print("manual_review=True")
        print("stopped=True")
        return 6

    print(f"success={control.success}")
    print(
        f"manual_review={control.requires_manual_review}"
    )
    print(f"stopped={control.stopped}")

    return 0 if control.success else 6


if __name__ == "__main__":
    raise SystemExit(main())
