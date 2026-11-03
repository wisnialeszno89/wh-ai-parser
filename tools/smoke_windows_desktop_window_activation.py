"""Interactive smoke test for safely activating one observed Windows window.

This tool changes focus only. It does not click, type, or modify the target app.
A unique process + title match and an explicit console confirmation are required.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.environment.windows_desktop_environment_adapter import (
    DesktopWindowSnapshot,
    WindowsDesktopEnvironmentAdapter,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.vision.bridges.execution_safety_gate import (
    ExecutionSafetyGate,
)


def select_target_window(
    windows: Sequence[DesktopWindowSnapshot],
    *,
    process_name: str,
    title_contains: str,
) -> DesktopWindowSnapshot:
    """Return exactly one visible, inactive window matching both selectors."""
    process_key = process_name.strip().casefold()
    title_key = title_contains.strip().casefold()
    if not process_key or not title_key:
        raise ValueError("activation_smoke_selectors_required")

    matches = [
        window
        for window in windows
        if isinstance(window, DesktopWindowSnapshot)
        and window.is_visible is True
        and window.is_foreground is False
        and isinstance(window.application, str)
        and window.application.strip().casefold() == process_key
        and isinstance(window.title, str)
        and title_key in window.title.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"activation_smoke_target_not_unique: matches={len(matches)}"
        )
    return matches[0]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Activate one uniquely matched window after explicit confirmation. "
            "The script never clicks or types into the target application."
        )
    )
    parser.add_argument(
        "--target-process",
        required=True,
        help="Exact process basename, for example Okna.exe",
    )
    parser.add_argument(
        "--target-title-contains",
        required=True,
        help="A title fragment that uniquely identifies the target window",
    )
    return parser.parse_args()


def main() -> int:
    if os.name != "nt":
        print("This smoke test requires Windows.")
        return 2

    args = _parse_args()
    adapter = WindowsDesktopEnvironmentAdapter()

    try:
        observation = adapter.observe()
    except Exception as exc:
        print(f"Could not observe the desktop: {type(exc).__name__}")
        return 2

    windows = observation.metadata.get("desktop_windows", ())
    if not isinstance(windows, (tuple, list)):
        print("Desktop window inventory has an invalid shape.")
        return 2

    try:
        target = select_target_window(
            windows,
            process_name=args.target_process,
            title_contains=args.target_title_contains,
        )
    except ValueError as exc:
        print(str(exc))
        print("No window was activated. Refine the process/title selectors.")
        return 2

    foreground_handle = observation.metadata.get(
        "foreground_window_handle",
        observation.metadata.get("window_handle"),
    )
    if (
        isinstance(foreground_handle, bool)
        or not isinstance(foreground_handle, int)
        or foreground_handle <= 0
        or target.handle == foreground_handle
    ):
        print("Foreground identity is missing or target is already active.")
        return 2

    observed_handles = tuple(
        window.handle
        for window in windows
        if isinstance(window, DesktopWindowSnapshot)
        and isinstance(window.handle, int)
        and not isinstance(window.handle, bool)
        and window.handle > 0
        and window.is_visible is True
    )
    if foreground_handle not in observed_handles or target.handle not in observed_handles:
        print("Target or foreground window is missing from the observed inventory.")
        return 2

    print("=== WINDOWS DESKTOP ACTIVATION SMOKE TEST ===")
    print(f"Current foreground application: {observation.state.active_application}")
    print(f"Target application: {target.application}")
    print(f"Target window: {target.title}")
    print("The test will only bring this window to the foreground.")
    print("It will not click, type, save, or change application data.")

    try:
        confirmation = input('Type "ACTIVATE" to proceed: ').strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled. No window was activated.")
        return 0

    if confirmation != "ACTIVATE":
        print("Cancelled. No window was activated.")
        return 0

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=ExecutionSafetyGate(),
        # This smoke test uses only the window activation path; avoid
        # constructing unrelated mouse/keyboard hardware adapters.
        mouse=SimpleNamespace(),
        keyboard=SimpleNamespace(),
    )
    result = executor.execute_window_activation(
        window_handle=target.handle,
        expected_foreground_handle=foreground_handle,
        observed_window_handles=observed_handles,
    )
    if not result.success or not result.executed:
        print(f"Activation was not confirmed: {result.reason}")
        return 1

    try:
        verified = adapter.observe()
    except Exception as exc:
        print(
            "Windows reported activation, but the follow-up observation failed: "
            f"{type(exc).__name__}"
        )
        return 1

    actual_foreground = verified.metadata.get("foreground_window_handle")
    if actual_foreground != target.handle:
        print("Postcondition failed: target is not the foreground window.")
        return 1

    print("SUCCESS: target window is now foreground.")
    print(f"Active application: {verified.state.active_application}")
    print(f"Active window: {verified.state.active_window_title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
