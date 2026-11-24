"""Read-only, one-shot observation of foreground WindowHub with no pinned OFR.

No keyboard, pointer input, document edits or model requests. Only bounded
stage and generic UIA metadata is emitted, never customer values or titles.
"""
from __future__ import annotations

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def describe_windowhub_scene(scene) -> tuple[str, ...]:
    from app.agent.learning.windowhub_demonstration import stage_of, semantic_snapshot
    try:
        state = scene.observation.state
        process = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
        if process != "okna.exe":
            return ("WINDOWHUB_FOREGROUND=False", "WINDOWHUB_STAGE=not_foreground")
        stage = stage_of(scene)
        known = {
            "start", "document_properties", "new_customer", "position",
            "dimensions", "basic_parameters", "glazing", "hardware",
            "modifier", "offer_document", "order_document", "windowhub_unmapped",
        }
        stage = stage if stage in known else "unmapped"
        snapshot = semantic_snapshot(scene)
        control_count = len(snapshot.get("controls", {})) if isinstance(snapshot, dict) else 0
        return (
            "WINDOWHUB_FOREGROUND=True",
            "WINDOWHUB_STAGE=" + stage,
            "WINDOWHUB_SAFE_UIA_CONTROLS=" + str(min(control_count, 150)),
            "WINDOWHUB_DOCUMENT_CONTENT_EXPORTED=False",
            "WINDOWHUB_NATIVE_ACTIONS=0",
        )
    except Exception:
        return ("WINDOWHUB_INSPECT=UNREADABLE", "WINDOWHUB_NATIVE_ACTIONS=0")


def run_inspection(*, observe=None, output=print) -> int:
    if observe is None and os.name != "nt":
        output("WINDOWHUB_INSPECT=WINDOWS_REQUIRED")
        return 2
    output("WINDOWHUB_INSPECT=REQUEST_STARTED")
    try:
        if observe is None:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                # Defense in depth: force dry-run even if shell requested LIVE.
                os.environ["COMPUTER_USE_LIVE"] = "0"
                from app.agent.runtime.windows_desktop_agent_control_loop import (
                    create_windows_desktop_agent_control_loop,
                )
                scene = create_windows_desktop_agent_control_loop().observe_scene()
            finally:
                pythoncom.CoUninitialize()
        else:
            scene = observe()
    except Exception:
        output("WINDOWHUB_INSPECT=OBSERVATION_FAILED")
        output("WINDOWHUB_NATIVE_ACTIONS=0")
        return 1
    for line in describe_windowhub_scene(scene):
        output(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_inspection())
