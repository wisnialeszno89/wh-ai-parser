"""Local WindowHub overall dimensions: one native write per field, no remote AI.

Default dry-run, with exact UIA observation. Live mode performs at most
one atomic replacement for width_1 then height_1; each write requires a
verified readback before proceeding. No Next, save or document commit.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.agent.runtime.windowhub_dimension_replace import (
    classify_replace, current_dimension, replace_dimension_once,
)


def run(width: int, height: int, execute_live: bool) -> int:
    if os.name != "nt" or not all(
        isinstance(n, int) and not isinstance(n, bool) and 100 <= n <= 5000
        for n in (width, height)
    ):
        print("STOP=invalid_dimensions_or_platform")
        return 2
    if any(os.getenv(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("STOP=desktop_authorization_flags_required")
        return 2
    activated, message = activate_windowhub_workflow_window()
    print("WINDOWHUB_ACTIVATION=" + message)
    if not activated:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    initial = loop.observe_scene()
    if stage_of(initial) != "dimensions":
        print("STOP=expected_dimensions_dialog")
        return 4
    desired = {"width_1": width, "height_1": height}
    for field, target in desired.items():
        value = current_dimension(initial, field)
        mode = classify_replace(value, target)
        print("DIMENSION_" + field.upper() + "_BEFORE=" + repr(value))
        print("DIMENSION_" + field.upper() + "_PLAN=" + mode)
        if mode == "unknown":
            print("STOP=dimension_value_unobservable")
            return 4
    if not execute_live:
        print("DRY_RUN_PASS=True")
        print("INPUT_EXECUTED=False")
        return 0
    for field, target in desired.items():
        outcome = replace_dimension_once(loop, field_name=field, desired=target)
        print("DIMENSION_" + field.upper() + "_STATUS=" + outcome.status)
        print("DIMENSION_" + field.upper() + "_REASON=" + outcome.reason)
        if outcome.status != "verified":
            print("STOP=dimension_not_verified_no_retry")
            return 5
    after = loop.observe_scene()
    if stage_of(after) != "dimensions" or any(
        (current_dimension(after, field) or "").strip() != str(target)
        for field, target in desired.items()
    ):
        print("DIMENSIONS_FINAL=NOT_VERIFIED")
        return 5
    print("DIMENSIONS_FINAL=VERIFIED")
    print("NEXT_ACTION=none_no_save_no_navigation")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify/set WindowHub overall width/height locally")
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.width, args.height, args.execute_live))
