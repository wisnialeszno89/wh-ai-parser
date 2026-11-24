"""Headless NaviMind control-panel verification demo, runs in Codespaces."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_panel_controller import NaviMindPanelController, PanelMode


def main() -> int:
    panel = NaviMindPanelController()
    print("PANEL_CONNECTED_TO_WINDOWHUB=" + str(panel.snapshot().connected))
    print("INITIAL_MODE=" + panel.snapshot().mode.value)
    panel.training()
    print("LEARNING_MODE=" + panel.snapshot().mode.value)
    panel.resume()
    print("AFTER_RESUME=" + panel.snapshot().mode.value)
    print("FRESH_OBSERVATION_REQUIRED=" + str(panel.arbiter.reobservation_required))
    print("INPUT_PERMIT_AVAILABLE=" + str(panel.current_permit() is not None))
    panel.takeover()
    print("AFTER_TAKEOVER=" + panel.snapshot().mode.value)
    panel.stop()
    print("AFTER_STOP=" + panel.snapshot().mode.value)
    print("CAN_RESUME_STOPPED_TASK=" + str(panel.snapshot().can_resume))
    print("REAL_GUI_ACTIONS_EXECUTED=False")
    return 0 if panel.snapshot().mode == PanelMode.STOPPED else 1


if __name__ == "__main__":
    raise SystemExit(main())
