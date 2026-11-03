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
    title_contains: str | None = None,
    title_must_be_empty: bool = False,
    root_window_only: bool = False,
) -> DesktopWindowSnapshot:
    """Return exactly one visible, inactive target window using explicit identity criteria."""
    process_key = process_name.strip().casefold()
    title_key = title_contains.strip().casefold() if isinstance(title_contains, str) else ""
    selector_count = sum((bool(title_key), title_must_be_empty, root_window_only))
    if not process_key or selector_count != 1:
        raise ValueError("activation_smoke_selectors_required")

    def identity_matches(window: DesktopWindowSnapshot) -> bool:
        if root_window_only:
            return window.root_owner_handle == window.handle
        if title_must_be_empty:
            return (
                (not isinstance(window.title, str) or not window.title.strip())
                and window.root_owner_handle == window.handle
            )
        return (
            isinstance(window.title, str)
            and title_key in window.title.casefold()
        )

    matches = [
        window
        for window in windows
        if isinstance(window, DesktopWindowSnapshot)
        and window.is_visible is True
        and window.is_foreground is False
        and isinstance(window.application, str)
        and window.application.strip().casefold() == process_key
        and identity_matches(window)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"activation_smoke_target_not_unique: matches={len(matches)}"
        )
    return matches[0]

def _print_target_diagnostics(
    windows: Sequence[DesktopWindowSnapshot],
    *,
    process_name: str,
    title_contains: str | None,
    title_must_be_empty: bool,
    root_window_only: bool,
    foreground_application: str | None,
    foreground_title: str | None,
) -> None:
    """Explain candidate selection without exposing native window handles."""
    process_key = process_name.strip().casefold()
    title_key = title_contains.strip().casefold() if isinstance(title_contains, str) else ""
    print("=== TARGET MATCH DIAGNOSTICS ===")
    print(f"Current foreground application: {foreground_application or 'unknown'}")
    print(f"Current foreground title: {foreground_title or '<BRAK TYTUŁU>'}")
    if root_window_only:
        selector = "<SAMODZIELNE OKNO GŁÓWNE>"
    elif title_must_be_empty:
        selector = "<BRAK TYTUŁU>"
    else:
        selector = repr(title_contains)
    print(f"Requested target selector: {selector}")
    candidates = [
        window
        for window in windows
        if isinstance(window, DesktopWindowSnapshot)
        and isinstance(window.application, str)
        and window.application.strip().casefold() == process_key
    ]
    print(f"Windows found for process {process_name}: {len(candidates)}")
    if not candidates:
        print("No enumerated window has the requested process name.")
        return

    for index, window in enumerate(candidates, start=1):
        has_title = isinstance(window.title, str) and bool(window.title.strip())
        title = window.title if has_title else "<BRAK TYTUŁU>"
        flags = []
        if window.is_foreground is True:
            flags.extend(("FOREGROUND", "ALREADY_FOREGROUND_NOT_ACTIVATED"))
        if window.is_minimized is True:
            flags.append("MINIMIZED")
        if window.is_visible is not True:
            flags.append("NOT_VISIBLE")
        if window.root_owner_handle == window.handle:
            flags.append("ROOT_OWNER_SELF")
        elif window.root_owner_handle is None:
            flags.append("ROOT_OWNER_UNKNOWN")
        else:
            flags.append("OWNED_BY_OTHER_WINDOW")
        if root_window_only:
            identity_ok = window.root_owner_handle == window.handle
        elif title_must_be_empty:
            identity_ok = not has_title and window.root_owner_handle == window.handle
            if has_title:
                flags.append("TITLE_PRESENT")
        else:
            identity_ok = has_title and title_key in title.casefold()
            if not identity_ok:
                flags.append("TITLE_MISMATCH")
        if identity_ok and window.is_visible is True and window.is_foreground is False:
            flags.append("MATCH_CANDIDATE")
        dimensions = (
            f"{window.rect.width}x{window.rect.height}"
            if window.rect is not None
            else "unknown-size"
        )
        print(
            f"{index:02d}. {window.application} — {title} ({dimensions})"
            + (f" [{' | '.join(flags)}]" if flags else "")
        )

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
    title_group = parser.add_mutually_exclusive_group(required=True)
    title_group.add_argument(
        "--target-title-contains",
        help="A real title fragment that uniquely identifies the target window",
    )
    title_group.add_argument(
        "--target-title-empty",
        action="store_true",
        help="Select a truly empty-title root window (not a display placeholder)",
    )
    title_group.add_argument(
        "--target-root-window",
        action="store_true",
        help="Select the uniquely identified independent root window for this process",
    )
    parser.add_argument(
        "--diagnose-only",
        action="store_true",
        help="Show the selected candidate and exit without activating any window",
    )
    return parser.parse_args()


def _configure_console_output() -> None:
    """Prevent unsupported Unicode characters in Windows titles from aborting output."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(errors="backslashreplace")


def main() -> int:
    _configure_console_output()

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
            title_must_be_empty=args.target_title_empty,
            root_window_only=args.target_root_window,
        )
    except ValueError as exc:
        print(str(exc))
        _print_target_diagnostics(
            windows,
            process_name=args.target_process,
            title_contains=args.target_title_contains,
            title_must_be_empty=args.target_title_empty,
            root_window_only=args.target_root_window,
            foreground_application=observation.state.active_application,
            foreground_title=observation.state.active_window_title,
        )
        print("No window was activated. Review the diagnostics before retrying.")
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
    print(f"Target window: {target.title or '<BRAK TYTUŁU>'}")
    print("The test will only bring this window to the foreground.")
    print("It will not click, type, save, or change application data.")

    if args.diagnose_only:
        print("DIAGNOSTICS ONLY: no window was activated.")
        return 0

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
