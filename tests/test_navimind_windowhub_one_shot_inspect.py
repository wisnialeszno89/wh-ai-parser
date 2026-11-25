"""Contract checks for real read-only, one-shot WindowHub scene inspection."""
from pathlib import Path
from types import SimpleNamespace

from tools.inspect_navimind_windowhub import (
    describe_windowhub_scene, run_inspection,
)


def scene(*, app="C:/Winkhaus/Okna.exe", title="Okna - Start1", elements=()):
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application=app, active_window_title=title),
            metadata={},
        ),
        elements=elements,
    )


def test_unrelated_foreground_does_not_report_windowhub():
    out = describe_windowhub_scene(
        scene(app="C:/Windows/notepad.exe", title="Prywatne dane")
    )
    assert "WINDOWHUB_FOREGROUND=False" in out
    assert "Prywatne dane" not in repr(out)


def test_start_stage_without_expected_offer():
    out = describe_windowhub_scene(scene())
    assert "WINDOWHUB_FOREGROUND=True" in out
    assert "WINDOWHUB_STAGE=start" in out
    assert "WINDOWHUB_NATIVE_ACTIONS=0" in out


def test_offer_stage_does_not_expose_title_or_customer():
    out = describe_windowhub_scene(scene(title="Okna - OFR/4811- TOP TRANS"))
    assert "WINDOWHUB_STAGE=offer_document" in out
    assert "4811" not in repr(out)
    assert "TOP TRANS" not in repr(out)


def test_single_observation_with_injected_reader_without_native_input():
    calls = []
    output = []
    def observer():
        calls.append("read")
        return scene()
    assert run_inspection(observe=observer, output=output.append) == 0
    assert calls == ["read"]
    assert output[0] == "WINDOWHUB_INSPECT=REQUEST_STARTED"
    assert "WINDOWHUB_STAGE=start" in output


def test_safe_observation_failure_no_exception_leak():
    output = []
    def fail():
        raise RuntimeError("private customer name 1234")
    assert run_inspection(observe=fail, output=output.append) == 1
    assert output[-1] == "WINDOWHUB_NATIVE_ACTIONS=0"
    assert "private" not in repr(output)


def test_owner_launcher_safely_exposes_explicit_inspect_mode():
    code = (Path(__file__).resolve().parents[1] / "tools" /
            "start_navimind_owner.ps1").read_text(encoding="utf-8")
    assert "[switch]$InspectWindowHub" in code
    assert 'python "tools/inspect_navimind_windowhub.py"' in code
    assert '$env:COMPUTER_USE_LIVE = "0"' in code
    assert "$DiagnoseChat -and $InspectWindowHub" in code


def test_uia_diagnostic_disambiguates_unmapped_controls_from_no_uia():
    def element(kind, source, visible, enabled, identifier=None):
        return SimpleNamespace(
            kind=kind,
            metadata={
                "source": source, "uia_visible": visible,
                "uia_enabled": enabled, "automation_id": identifier,
            },
        )
    observed = scene(elements=[
        element("button", "windows_ui_automation", True, True, "BTN_NEW"),
        element("button", "windows_ui_automation", True, True, "IDC_NEW"),
        element("text", "windows_ui_automation", True, False, None),
        element("button", "windows_ui_automation", False, True, "IDC_HIDDEN"),
        element("application_window", "windows_desktop_window", True, True),
    ])
    from tools.inspect_navimind_windowhub import summarize_uia_visibility
    counts = summarize_uia_visibility(observed)
    assert "WINDOWHUB_UIA_ELEMENTS=4" in counts
    assert "WINDOWHUB_UIA_VISIBLE=3" in counts
    assert "WINDOWHUB_UIA_ENABLED_VISIBLE=2" in counts
    assert "WINDOWHUB_UIA_INTERACTIVE_VISIBLE=2" in counts
    assert "WINDOWHUB_UIA_INTERACTIVE_WITH_ID=2" in counts
    assert "WINDOWHUB_UIA_INTERACTIVE_MAPPED_ID=1" in counts
    assert not any("BTN_NEW" in item for item in counts)


def test_empty_uia_scene_reports_zero_counts():
    counts = describe_windowhub_scene(scene())
    assert "WINDOWHUB_UIA_ELEMENTS=0" in counts
    assert "WINDOWHUB_UIA_INTERACTIVE_VISIBLE=0" in counts
    assert "WINDOWHUB_NATIVE_ACTIONS=0" in counts


def test_background_discovery_finds_okna_without_focus():
    from tools.inspect_navimind_windowhub import locate_windowhub_windows
    windows = [
        SimpleNamespace(application="C:/Windows/firefox.exe", is_visible=True, is_foreground=True, is_minimized=False),
        SimpleNamespace(application="C:/Winkhaus/OKNA.EXE", is_visible=True, is_foreground=False, is_minimized=False),
    ]
    output = locate_windowhub_windows(windows)
    assert "WINDOWHUB_DISCOVERY=FOUND" in output
    assert "WINDOWHUB_FOUND_WINDOWS=1" in output
    assert "WINDOWHUB_IS_FOREGROUND=False" in output
    assert "WINDOWHUB_NATIVE_ACTIONS=0" in output
    assert "firefox" not in repr(output)


def test_background_discovery_does_not_claim_hidden_or_unrelated_app():
    from tools.inspect_navimind_windowhub import locate_windowhub_windows
    out = locate_windowhub_windows([
        SimpleNamespace(application="okna.exe", is_visible=False, is_foreground=False),
        SimpleNamespace(application="word.exe", is_visible=True, is_foreground=True),
    ])
    assert "WINDOWHUB_DISCOVERY=NOT_FOUND" in out


def test_background_discovery_reports_minimized_state_not_ui_readiness():
    from tools.inspect_navimind_windowhub import locate_windowhub_windows
    out = locate_windowhub_windows([
        SimpleNamespace(application="OKNA.EXE", is_visible=True, is_foreground=False, is_minimized=True),
    ])
    assert "WINDOWHUB_ALL_MINIMIZED=True" in out
    assert not any("STAGE=" in item for item in out)


def test_discovery_reads_injected_window_inventory_once():
    from tools.inspect_navimind_windowhub import run_discovery
    out = []
    inventory = [
        SimpleNamespace(application="okna.exe", is_visible=True,
                        is_foreground=False, is_minimized=False),
    ]
    assert run_discovery(inventory=inventory, output=out.append) == 0
    assert "WINDOWHUB_DISCOVERY=FOUND" in out


def test_owner_launcher_supports_discovery_without_previous_ofr():
    code = (Path(__file__).resolve().parents[1] / "tools" /
            "start_navimind_owner.ps1").read_text(encoding="utf-8")
    assert "[switch]$FindWindowHub" in code
    assert "run_discovery()" in code
    assert '$env:COMPUTER_USE_LIVE = "0"' in code
