from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.runtime.verification_loop import VerificationLoop
from app.agent.verification.expectation_resolver import ExpectationResolver
from app.agent.verification.outcome_verifier import OutcomeVerifier
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.agent.environment.environment_state import EnvironmentState

from tools.inspect_live_windowhub_ui_targets import (
    _windowhub_hwnd,
    _window_title,
)
from tools.live_click_windowhub_target import _focus_window


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one semantic click through the main RobotGUIExecutor "
            "against the real WindowHub environment."
        )
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Exact semantic target label.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable one real mouse click.",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="Seconds to wait after focusing WindowHub.",
    )
    return parser.parse_args()


def build_perception() -> PerceptionEngine:
    return PerceptionEngine(
        providers=(
            WindowHubVisionProvider(),
            WindowHubUIAutomationProvider(),
        )
    )


def build_context(
    environment: WindowHubEnvironmentAdapter,
    perception: PerceptionEngine,
) -> ExecutionContext:
    observation = environment.observe()
    scene = perception.perceive(observation)

    context = ExecutionContext(
        request=AgentRequest(
            message="Perform one controlled GUI click."
        )
    )
    context.update_scene(scene)
    return context


def print_scene_target(
    context: ExecutionContext,
    target: str,
) -> None:
    scene = context.current_scene
    if scene is None:
        raise RuntimeError("Initial scene is unavailable.")

    print(
        f"initial_scene_elements={len(scene.elements)}"
    )

    matches = [
        element
        for element in scene.elements
        if (
            element.label is not None
            and element.label.casefold() == target.casefold()
        )
    ]

    print(f"semantic_matches={len(matches)}")

    for element in matches:
        metadata = dict(element.metadata or {})
        print(
            "target_candidate="
            f"label={element.label!r} "
            f"kind={element.kind!r} "
            f"bounds=({element.x},{element.y},{element.width},{element.height}) "
            f"source={metadata.get('source')!r} "
            f"automation_id={metadata.get('automation_id')!r} "
            f"uia_enabled={metadata.get('uia_enabled')!r} "
            f"uia_visible={metadata.get('uia_visible')!r} "
            f"tracked_object_id={metadata.get('tracked_object_id')!r}"
        )


def main() -> int:
    args = parse_args()

    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("Set WH_REAL_WINDOWHUB=1 before running this smoke-test.")
        return 2

    hwnd = _windowhub_hwnd()
    if hwnd is None:
        print("No visible WindowHub main window was found.")
        return 3

    print("Main RobotGUIExecutor WindowHub smoke-test")
    print("===========================================")
    print(f"windowhub_hwnd={hwnd}")
    print(f"windowhub_title={_window_title(hwnd)!r}")
    print(f"target={args.target!r}")
    print(
        "mode="
        + ("LIVE" if args.execute else "DRY_RUN")
    )

    if not _focus_window(hwnd):
        print(
            "ABORTED: WindowHub could not be made the foreground window."
        )
        return 4

    time.sleep(max(0.0, args.wait))

    environment = WindowHubEnvironmentAdapter()
    perception = build_perception()

    context = build_context(
        environment,
        perception,
    )

    observation = context.last_observation
    if observation is None:
        print("ABORTED: WindowHub observation is unavailable.")
        return 5

    observed_handle = observation.metadata.get("window_handle")
    if observed_handle != hwnd:
        print(
            "ABORTED: observation/window handle mismatch: "
            f"observed={observed_handle!r} expected={hwnd!r}"
        )
        return 6

    print_scene_target(
        context,
        args.target,
    )

    robot = RobotActionExecutor(
        mode=(
            RobotExecutionMode.LIVE
            if args.execute
            else RobotExecutionMode.DRY_RUN
        )
    )

    gui_executor = RobotGUIExecutor(
        robot_action_executor=robot,
    )

    registry = ExecutorRegistry(
        executors=(gui_executor,)
    )

    engine = ExecutionEngine(
        registry=registry,
    )

    loop = VerificationLoop(
        execution_engine=engine,
        environment=environment,
        perception_engine=perception,
        expectation_resolver=ExpectationResolver(),
        outcome_verifier=OutcomeVerifier(),
        max_attempts=1,
    )

    action = AgentAction(
        name="click_screen_element",
        description=f"Click {args.target}",
        target=args.target,
    )

    if args.execute:
        if not _focus_window(hwnd):
            print(
                "ABORTED: WindowHub lost foreground status "
                "before the execution boundary."
            )
            return 7

    result = loop.run(
        action,
        context,
    )

    print()
    print("=== EXECUTION ===")
    for index, attempt in enumerate(
        result.attempts,
        start=1,
    ):
        execution = attempt.execution_result
        verification = attempt.verification_result

        print(
            f"attempt[{index}] "
            f"execution_success={getattr(execution, 'success', None)} "
            f"execution_executed={getattr(execution, 'metadata', {}).get('executed') if execution else None} "
            f"execution_path={getattr(execution, 'metadata', {}).get('execution_path') if execution else None}"
        )

        if execution is not None:
            print(
                f"execution_message={execution.message!r}"
            )
            print(
                f"execution_metadata={execution.metadata!r}"
            )

        print(
            f"verification_verified="
            f"{getattr(verification, 'verified', None)}"
        )

        if verification is not None:
            print(
                f"verification_reason={verification.reason!r}"
            )
            print(
                f"verification_metadata={verification.metadata!r}"
            )

    print()
    print("=== FINAL ===")
    print(f"success={result.success}")
    print(
        "requires_manual_review="
        f"{result.requires_manual_review}"
    )
    print(f"stopped={result.stopped}")
    print(f"attempt_count={len(result.attempts)}")

    return 0 if result.success else 8


if __name__ == "__main__":
    raise SystemExit(main())
