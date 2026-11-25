"""Preflight never contacts WindowHub, Vercel, PDFs or local secrets."""
from tools.run_navimind_offer_preflight import inspect_local_preflight


def test_offline_preflight_reports_missing_components_without_secret_contents():
    report = inspect_local_preflight(
        environ={"NAVIMIND_AGENT_SECRET": "top-secret-in-memory"},
        module_probe=lambda name: name == "fitz",
        system="Linux", python_version=(3, 13),
    )
    assert report["read_only_preflight"]
    assert not report["real_desktop_test_completed"]
    assert not report["network_checked"]
    assert not report["windowhub_observed"]
    assert "requires_windows_desktop" in report["warnings"]
    assert "native_input_not_armed" in report["warnings"]
    assert "missing_pywinauto" in report["warnings"]
    assert "top-secret-in-memory" not in repr(report)


def test_fully_configured_flags_are_report_only_not_execution_permission():
    env = {
        "WH_REAL_WINDOWHUB": "1", "COMPUTER_USE_LIVE": "1",
        "NAVIMIND_AGENT_V2_URL": "https://gateway.example.invalid/api",
        "NAVIMIND_AGENT_SECRET": "secret",
    }
    report = inspect_local_preflight(
        environ=env, module_probe=lambda _: True,
        system="Windows", python_version=(3, 13),
    )
    assert report["warnings"] == []
    assert report["live_flags_both_enabled"]
    assert report["read_only_preflight"]
    assert report["network_checked"] is False
    assert "secret" not in repr(report)
    assert "gateway.example.invalid" not in repr(report)


def test_single_live_flag_does_not_count_as_armed():
    report = inspect_local_preflight(
        environ={"WH_REAL_WINDOWHUB": "1"},
        module_probe=lambda _: True,
        system="Windows", python_version=(3, 13),
    )
    assert not report["live_flags_both_enabled"]
