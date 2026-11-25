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
        "NAVIMIND_AGENT_V2_SECRET": "NAVI_TEST_ONLY_CREDENTIAL_ABC123",
    }
    report = inspect_local_preflight(
        environ=env, module_probe=lambda _: True,
        system="Windows", python_version=(3, 13),
    )
    assert report["warnings"] == []
    assert report["live_flags_both_enabled"]
    assert report["read_only_preflight"]
    assert report["network_checked"] is False
    assert env["NAVIMIND_AGENT_V2_SECRET"] not in repr(report)
    assert "gateway.example.invalid" not in repr(report)


def test_single_live_flag_does_not_count_as_armed():
    report = inspect_local_preflight(
        environ={"WH_REAL_WINDOWHUB": "1"},
        module_probe=lambda _: True,
        system="Windows", python_version=(3, 13),
    )
    assert not report["live_flags_both_enabled"]


def test_v2_endpoint_requires_the_matching_v2_secret_and_reports_sso_bypass():
    env = {
        "NAVIMIND_AGENT_V2_URL": "https://private.vercel.app/api/agent/task",
        "NAVIMIND_AGENT_SECRET": "old-shared-secret",
        "WH_REAL_WINDOWHUB": "1", "COMPUTER_USE_LIVE": "1",
    }
    report = inspect_local_preflight(
        environ=env, module_probe=lambda _: True,
        system="Windows", python_version=(3, 13),
    )
    assert not report["reasoner_secret_configured"]
    assert "reasoner_secret_not_configured_in_process" in report["warnings"]
    assert "vercel_sso_may_require_automation_bypass" in report["warnings"]
    env["NAVIMIND_AGENT_V2_SECRET"] = "private-v2-secret"
    env["NAVIMIND_VERCEL_PROTECTION_BYPASS"] = "different-private-bypass"
    updated = inspect_local_preflight(
        environ=env, module_probe=lambda _: True,
        system="Windows", python_version=(3, 13),
    )
    assert updated["reasoner_secret_configured"]
    assert updated["vercel_automation_bypass_configured"]
    assert updated["warnings"] == []
    assert "different-private-bypass" not in repr(updated)
    assert "private-v2-secret" not in repr(updated)
