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
            "Run one goal-driven autonomous WindowHub offer smoke-test. "
            "The request is sent once; the runtime loops internally through "
            "observe -> reason -> act -> verify cycles."
        )
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=12,
        help="Maximum number of autonomous observe/reason/action cycles.",
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


def _print_result(turn: int, result, runtime) -> None:
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

        planner = getattr(
            runtime.orchestrator,
            "task_planner",
            None,
        )
        print(
            "reasoning_failure="
            f"{getattr(planner, 'last_failure_reason', None)!r}"
        )

        offer_planning = result.context.get_value(
            "offer_workflow_planning"
        )
        print(
            "offer_workflow="
            f"{offer_planning!r}"
        )

        scene = result.context.current_scene
        if scene is None:
            print("scene=None")
        else:
            print(
                "scene_application="
                f"{scene.observation.state.active_application!r}"
            )
            print(
                "scene_window="
                f"{scene.observation.state.active_window_title!r}"
            )
            print("scene_visible_elements:")
            for element in scene.elements[:120]:
                print(
                    "  "
                    f"kind={element.kind!r} "
                    f"label={element.label!r} "
                    f"capability={element.interaction_capability.value!r} "
                    f"confidence={element.confidence!r}"
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
    print(f"max_steps={args.max_steps}")
    print(f"scenario={message}")

    task_planner = getattr(
        runtime.orchestrator,
        "task_planner",
        None,
    )
    print(
        "task_reasoner="
        f"{type(getattr(task_planner, 'reasoner', None)).__name__}"
    )
    print(
        "plan_reasoner="
        f"{type(getattr(getattr(runtime.control_loop, 'replanner', None), 'reasoner', None)).__name__}"
    )
    reasoner = getattr(
        task_planner,
        "reasoner",
        None,
    )
    print(
        "task_vision="
        f"{getattr(getattr(reasoner, 'config', None), 'include_screenshot', None)}"
    )

    task_planner = getattr(
        runtime.orchestrator,
        "task_planner",
        None,
    )
    print(
        "task_reasoner="
        f"{type(getattr(task_planner, 'reasoner', None)).__name__}"
    )
    print(
        "plan_reasoner="
        f"{type(getattr(getattr(runtime.control_loop, 'replanner', None), 'reasoner', None)).__name__}"
    )

    autonomous = runtime.run_autonomous(
        AgentRequest(
            message=message,
            session_id=session_id,
        ),
        max_steps=max(1, args.max_steps),
    )

    for step_number, result in enumerate(
        autonomous.step_results,
        start=1,
    ):
        _print_result(step_number, result, runtime)

    print()
    print("=== FINAL ===")
    print(f"success={autonomous.success}")
    print(f"completed={autonomous.completed}")
    print(f"manual_review={autonomous.requires_manual_review}")
    print(f"stopped={autonomous.stopped}")
    print(f"reason={autonomous.reason!r}")
    print(f"session_id={autonomous.session_id!r}")
    print(f"executed_actions={autonomous.executed_actions}")

    return 0 if autonomous.success else 6


if __name__ == "__main__":
    raise SystemExit(main())
