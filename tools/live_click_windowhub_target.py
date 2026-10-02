from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.perception.target_resolver import TargetResolver
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)
from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.window.window_rect import WindowRect
from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine

from tools.inspect_live_windowhub_ui_targets import (
    _windowhub_hwnd,
    _window_rect,
    _window_title,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Controlled single-target WindowHub click probe."
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Exact semantic target label or tracked object id.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute one real mouse click after all safety checks pass.",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=5.0,
        help="Seconds allowed to bring WindowHub to the foreground before LIVE execution.",
    )
    parser.add_argument(
        "--uia-only",
        action="store_true",
        help=(
            "Allow an explicitly requested exact UIA target to execute "
            "without a correlated visual tracked object. This mode still "
            "requires an enabled, visible, clickable UIA element and a "
            "foreground WindowHub boundary check."
        ),
    )
    return parser.parse_args()


def _build_scene(hwnd: int):
    rect = _window_rect(hwnd)
    title = _window_title(hwnd)

    if not rect:
        raise RuntimeError("WindowHub geometry is unavailable.")

    left, top, width, height = rect
    if width <= 0 or height <= 0:
        raise RuntimeError(
            f"WindowHub geometry is invalid: {rect!r}"
        )

    window_rect = WindowRect(
        left=left,
        top=top,
        width=width,
        height=height,
    )

    screenshot = MSSScreenshotEngine().capture(window_rect)

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application=None,
            active_window_title=title,
            screen_width=screenshot.width,
            screen_height=screenshot.height,
        ),
        metadata={
            "source": "windowhub",
            "screenshot": screenshot,
            "window_rect": window_rect,
            "window_handle": hwnd,
        },
    )

    perception = PerceptionEngine(
        providers=(
            WindowHubVisionProvider(),
            WindowHubUIAutomationProvider(),
        ),
    )

    scene = perception.perceive(observation)

    return observation, scene, window_rect


def _find_target(scene, target: str, *, allow_uia_only: bool):
    resolution = TargetResolver().resolve(scene, target)

    if not resolution.resolved or resolution.element is None:
        raise RuntimeError(
            f"Target resolution failed: {resolution.reason}"
        )

    element = resolution.element
    metadata = dict(element.metadata or {})

    if metadata.get("source") != "windowhub_ui_automation" and (
        "windowhub_ui_automation" not in (
            metadata.get("fusion_sources") or ()
        )
    ):
        raise RuntimeError(
            "Resolved target is not grounded in live WindowHub UI Automation."
        )

    if metadata.get("uia_enabled") is not True:
        raise RuntimeError(
            "Resolved target is not enabled."
        )

    if metadata.get("uia_visible") is not True:
        raise RuntimeError(
            "Resolved target is not visible."
        )

    if element.interaction_capability is not InteractionCapability.CLICKABLE:
        raise RuntimeError(
            "Resolved target is not clickable."
        )

    tracked_id = metadata.get("tracked_object_id")
    if not isinstance(tracked_id, str) or not tracked_id:
        if not allow_uia_only:
            raise RuntimeError(
                "Resolved target has no unique tracked object id. "
                "Use --uia-only only for an explicitly requested exact UIA target."
            )

        return resolution, element, None, None

    tracked_objects = (
        scene.metadata.get("execution_runtime", {})
        .get("robot_tracked_objects", ())
    )

    tracked_object = next(
        (
            item
            for item in tracked_objects
            if getattr(item, "id", None) == tracked_id
        ),
        None,
    )

    if tracked_object is None:
        raise RuntimeError(
            f"Tracked object {tracked_id!r} is unavailable."
        )

    root = (
        scene.metadata.get("execution_runtime", {})
        .get("gui_object_root")
    )

    if root is None:
        raise RuntimeError(
            "GUI object root is unavailable."
        )

    return resolution, element, tracked_object, root


def _foreground_hwnd() -> int:
    import ctypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    return int(user32.GetForegroundWindow())


def _focus_window(hwnd: int) -> bool:
    import ctypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    SW_RESTORE = 9

    if not user32.IsWindow(ctypes.c_void_p(hwnd)):
        return False

    user32.ShowWindow(ctypes.c_void_p(hwnd), SW_RESTORE)
    user32.BringWindowToTop(ctypes.c_void_p(hwnd))
    user32.SetForegroundWindow(ctypes.c_void_p(hwnd))

    for _ in range(20):
        if _foreground_hwnd() == hwnd:
            return True
        time.sleep(0.05)

    # Windows may block direct activation when another process owns the
    # foreground thread. Bridge the two input queues for this short
    # activation attempt, then detach immediately.
    current_foreground = _foreground_hwnd()
    if current_foreground <= 0:
        return False

    foreground_thread = user32.GetWindowThreadProcessId(
        ctypes.c_void_p(current_foreground),
        None,
    )
    target_thread = user32.GetWindowThreadProcessId(
        ctypes.c_void_p(hwnd),
        None,
    )

    if foreground_thread and target_thread and foreground_thread != target_thread:
        attached = bool(
            user32.AttachThreadInput(
                foreground_thread,
                target_thread,
                True,
            )
        )
        try:
            user32.SetForegroundWindow(ctypes.c_void_p(hwnd))
            user32.BringWindowToTop(ctypes.c_void_p(hwnd))
            time.sleep(0.1)
        finally:
            if attached:
                user32.AttachThreadInput(
                    foreground_thread,
                    target_thread,
                    False,
                )

    return _foreground_hwnd() == hwnd


def main() -> int:
    args = _parse_args()

    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("Set WH_REAL_WINDOWHUB=1 before running this probe.")
        return 2

    hwnd = _windowhub_hwnd()
    if hwnd is None:
        print("No visible WindowHub main window was found.")
        return 3

    print("WindowHub single-click probe")
    print("============================")
    print(f"windowhub_hwnd={hwnd}")
    print(f"windowhub_title={_window_title(hwnd)!r}")
    print(f"target={args.target!r}")
    mode = "LIVE_UIA_ONLY" if args.execute and args.uia_only else (
        "LIVE" if args.execute else (
            "DRY_RUN_UIA_ONLY" if args.uia_only else "DRY_RUN"
        )
    )
    print(f"mode={mode}")
    print("No click is executed unless --execute is supplied.")
    print()

    if args.execute:
        print(
            f"Focusing WindowHub and waiting {args.wait:.1f}s "
            "before the execution boundary."
        )

        if not _focus_window(hwnd):
            print(
                "ABORTED: Windows did not grant foreground status "
                "to the WindowHub window."
            )
            return 4

        time.sleep(max(0.0, args.wait))

        if not _focus_window(hwnd):
            print(
                "ABORTED: WindowHub lost foreground status before "
                "the execution boundary."
            )
            return 4

    try:
        observation, scene, window_rect = _build_scene(hwnd)
        resolution, element, tracked_object, root = _find_target(
            scene,
            args.target,
            allow_uia_only=args.uia_only,
        )
    except Exception as exc:
        print(f"ABORTED: {exc}")

        try:
            print()
            print("=== CURRENT UIA TARGETS ===")
            for item in scene.elements:
                metadata = dict(item.metadata or {})
                if (
                    metadata.get("source") != "windowhub_ui_automation"
                    and "uia_control_type" not in metadata
                ):
                    continue

                print(
                    repr(item.label),
                    "| AutomationId=",
                    repr(metadata.get("automation_id")),
                    "| control=",
                    repr(metadata.get("uia_control_type")),
                    "| enabled=",
                    metadata.get("uia_enabled"),
                    "| visible=",
                    metadata.get("uia_visible"),
                    "| tracked=",
                    repr(metadata.get("tracked_object_id")),
                )
        except Exception as dump_exc:
            print(f"Could not dump current UIA targets: {dump_exc}")

        return 5

    metadata = dict(element.metadata or {})
    local_bounds = (
        int(element.x),
        int(element.y),
        int(element.width),
        int(element.height),
    )
    screen_point = (
        window_rect.left + element.x + element.width // 2,
        window_rect.top + element.y + element.height // 2,
    )

    print(f"resolved_label={element.label!r}")
    print(f"automation_id={metadata.get('automation_id')!r}")
    print(f"tracked_object_id={metadata.get('tracked_object_id')!r}")
    print(f"interaction_capability={element.interaction_capability.value}")
    print(f"local_bounds={local_bounds}")
    print(f"screen_point={screen_point}")
    print(f"resolution_score={resolution.score}")

    if not args.execute:
        print()
        if args.uia_only and not metadata.get("tracked_object_id"):
            print(
                "DRY-RUN UIA-ONLY OK: semantic target is valid; "
                "no hardware action was executed."
            )
        else:
            print("DRY-RUN OK: no hardware action was executed.")
        return 0

    if args.uia_only and not metadata.get("tracked_object_id"):
        if _foreground_hwnd() != hwnd:
            print(
                "ABORTED: WindowHub lost foreground status after perception "
                "and before the UIA-only click."
            )
            return 7

        mouse = RobotMouse(mode=RobotMouseMode.LIVE)
        mouse_result = mouse.click(*screen_point)

        print(f"executed={mouse_result.executed}")
        print(f"success={mouse_result.success}")
        print(f"point={mouse_result.point}")
        print(f"reason={mouse_result.reason}")

        return 0 if mouse_result.success and mouse_result.executed else 6

    confidence = metadata.get(
        "interaction_capability_confidence"
    )
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = None

    expected_control_type = getattr(
        tracked_object,
        "control_type",
        ControlType.UNKNOWN,
    )

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
    )

    result = executor.execute(
        tracked_object=tracked_object,
        action=InteractionAction.CLICK,
        root=root,
        expected_control_type=expected_control_type,
        expected_bounds=tracked_object.object.bounds,
        interaction_capability=element.interaction_capability,
        interaction_capability_confidence=confidence,
        screen_origin=(
            int(window_rect.left),
            int(window_rect.top),
        ),
    )

    print(f"executed={result.executed}")
    print(f"success={result.success}")
    print(f"point={result.point}")
    print(f"reason={result.reason}")

    return 0 if result.success and result.executed else 6


if __name__ == "__main__":
    raise SystemExit(main())
