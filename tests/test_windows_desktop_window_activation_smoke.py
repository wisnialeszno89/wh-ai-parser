import sys

import pytest

from app.agent.environment.windows_desktop_environment_adapter import (
    DesktopWindowSnapshot,
)
from app.runtime.execution.window.window_rect import WindowRect
from tools.smoke_windows_desktop_window_activation import (
    _configure_console_output as configure_activation_console,
    _print_target_diagnostics,
    select_target_window,
)
from tools.smoke_windows_desktop_window_inventory import (
    _configure_console_output as configure_inventory_console,
)


def _window(
    application,
    title,
    *,
    handle,
    foreground=False,
    visible=True,
):
    return DesktopWindowSnapshot(
        handle=handle,
        title=title,
        rect=WindowRect(left=0, top=0, width=800, height=600),
        application=application,
        root_owner_handle=handle,
        is_foreground=foreground,
        is_visible=visible,
    )


def test_activation_smoke_selects_one_inactive_window_by_process_and_title():
    foreground = _window(
        "Code.exe",
        "workspace",
        handle=100,
        foreground=True,
    )
    target = _window(
        "Okna.exe",
        "Untitled window",
        handle=200,
    )
    other = _window(
        "Okna.exe",
        "Offer OFR-123",
        handle=300,
    )

    selected = select_target_window(
        (foreground, target, other),
        process_name="okna.EXE",
        title_contains="untitled",
    )

    assert selected is target


def test_activation_smoke_rejects_ambiguous_target_instead_of_guessing():
    windows = (
        _window("Okna.exe", "Untitled window 1", handle=200),
        _window("Okna.exe", "Untitled window 2", handle=300),
    )

    with pytest.raises(
        ValueError,
        match="activation_smoke_target_not_unique: matches=2",
    ):
        select_target_window(
            windows,
            process_name="Okna.exe",
            title_contains="Untitled",
        )


def test_activation_smoke_rejects_missing_or_blank_selectors():
    windows = (_window("Okna.exe", "Untitled window", handle=200),)

    with pytest.raises(ValueError, match="activation_smoke_selectors_required"):
        select_target_window(
            windows,
            process_name=" ",
            title_contains="Untitled",
        )

    with pytest.raises(ValueError, match="activation_smoke_selectors_required"):
        select_target_window(
            windows,
            process_name="Okna.exe",
            title_contains=" ",
        )


def test_activation_smoke_never_selects_foreground_or_invisible_windows():
    windows = (
        _window(
            "Okna.exe",
            "Foreground",
            handle=200,
            foreground=True,
        ),
        _window(
            "Okna.exe",
            "Hidden",
            handle=300,
            visible=False,
        ),
    )

    with pytest.raises(
        ValueError,
        match="activation_smoke_target_not_unique: matches=0",
    ):
        select_target_window(
            windows,
            process_name="Okna.exe",
            title_contains="i",
        )



@pytest.mark.parametrize(
    "configure_console",
    (configure_inventory_console, configure_activation_console),
)
def test_smoke_scripts_escape_unicode_characters_unsupported_by_console(
    monkeypatch,
    configure_console,
):
    calls = []

    class _FakeStdout:
        def reconfigure(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(sys, "stdout", _FakeStdout())

    configure_console()

    assert calls == [{"errors": "backslashreplace"}]



def test_activation_diagnostics_explain_foreground_and_title_mismatches(
    capsys,
):
    windows = (
        _window(
            "Okna.exe",
            "Untitled window",
            handle=200,
            foreground=True,
        ),
        _window(
            "Okna.exe",
            "Okna - OFR/4522-",
            handle=300,
        ),
    )

    _print_target_diagnostics(
        windows,
        process_name="Okna.exe",
        title_contains="Untitled window",
        foreground_application="Okna.exe",
        foreground_title="Untitled window",
    )

    output = capsys.readouterr().out
    assert "Windows found for process Okna.exe: 2" in output
    assert "FOREGROUND" in output
    assert "ALREADY_FOREGROUND_NOT_ACTIVATED" in output
    assert "TITLE_MISMATCH" in output
    assert "200" not in output
    assert "300" not in output
