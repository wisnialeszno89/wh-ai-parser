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
