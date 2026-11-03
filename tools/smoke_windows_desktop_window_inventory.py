"""Read-only smoke test for visible Windows desktop window enumeration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Direct execution (python tools/...) puts tools/ on sys.path, not the
# repository root. Add the project root before importing the application.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.environment.windows_desktop_environment_adapter import (
    DesktopWindowSnapshot,
    WindowsDesktopEnvironmentAdapter,
)


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

    observation = WindowsDesktopEnvironmentAdapter().observe()
    windows = observation.metadata.get("desktop_windows", ())
    if not isinstance(windows, (tuple, list)):
        print("Desktop window inventory has an invalid shape.")
        return 2

    print("=== WINDOWS DESKTOP WINDOW INVENTORY (READ ONLY) ===")
    print(f"Active application: {observation.state.active_application}")
    print(f"Active window: {observation.state.active_window_title}")
    print(f"Visible top-level windows: {len(windows)}")

    for index, window in enumerate(windows, start=1):
        if not isinstance(window, DesktopWindowSnapshot):
            continue
        flags = []
        if window.is_foreground:
            flags.append("FOREGROUND")
        if window.is_minimized:
            flags.append("MINIMIZED")
        status = f" [{' | '.join(flags)}]" if flags else ""
        title = window.title or "Untitled window"
        application = window.application or "unknown application"
        print(f"{index:02d}. {application} — {title}{status}")

    return 0 if windows else 1


if __name__ == "__main__":
    raise SystemExit(main())
