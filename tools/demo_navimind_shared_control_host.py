"""Portable shared-host demo. No Windows, WindowHub or GUI needed."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_local_input_arbiter import InputDenied
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost


def scene(*, offer="OFR/DEMO", width="1200"):
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application="Okna.exe",
                                  active_window_title="Okna - " + offer),
            metadata={"window_handle": 81},
        ),
        elements=(
            SimpleNamespace(kind="tabitem", label=offer, metadata={
                "source": "windows_ui_automation", "uia_tab_scope": "document",
                "uia_selected": True, "uia_visible": True,
                "uia_runtime_id": "tab-1", "automation_id": "DOC_TAB",
            }),
            SimpleNamespace(kind="edit", label="Szerokość", metadata={
                "source": "windows_ui_automation", "uia_visible": True,
                "uia_enabled": True, "uia_runtime_id": "field-1",
                "automation_id": "IDC_WIDTH", "current_value": width,
            }),
        ),
    )


def main() -> int:
    host = NaviMindSharedHost("OFR/DEMO")
    print("HOST_CONNECTED=" + str(host.controller.snapshot().connected))
    print("INITIAL_HUMAN_CONTROL=" + str(host.controller.snapshot().human_controls))
    host.release_for_reobservation()
    print("RESUME_PENDING=" + str(host.controller.snapshot().mode.value == "resume_pending"))
    proof = host.inspect_fresh_scene(scene())
    print("OFFER_VERIFIED=" + str(proof.verified))
    print("INPUT_PERMIT_AVAILABLE=" + str(host.controller.current_permit() is not None))
    host.takeover()
    try:
        host.guarded_dispatch(None, lambda: None)
        blocked = False
    except InputDenied:
        blocked = True
    print("STALE_ACTION_BLOCKED_AFTER_TAKEOVER=" + str(blocked))
    host.stop()
    print("AFTER_STOP=" + host.controller.snapshot().mode.value)
    print("LIVE_WINDOWHUB_CONNECTED=False")
    print("REAL_GUI_ACTIONS_EXECUTED=False")
    return 0 if proof.verified and blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
