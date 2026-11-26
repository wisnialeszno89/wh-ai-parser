"""The desktop host must distinguish GUI lifecycle from preflight and V2 readiness."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shared_host_reports_mainloop_start_visibility_and_exit():
    source = (ROOT / "tools/run_navimind_shared_control_center.py").read_text(
        encoding="utf-8"
    )
    assert "NAVIMIND_PANEL_MAINLOOP_ENTERED=True" in source
    assert "NAVIMIND_PANEL_WINDOW_STATE=" in source
    assert "NAVIMIND_PANEL_MAINLOOP_EXITED=True" in source
    assert "CLOSE_REQUESTED=" in source
    assert "NAVIMIND_PANEL_MAINLOOP_FAILED=" in source
    assert "panel.after(400, window_visibility_probe)" in source


def test_preflight_is_not_the_gui_launcher():
    source = (ROOT / "tools/run_navimind_offer_preflight.py").read_text(
        encoding="utf-8"
    )
    assert "read-only" in source.lower()
    assert "tkinter" not in source
