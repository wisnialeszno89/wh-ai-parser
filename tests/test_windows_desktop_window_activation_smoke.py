import sys

import pytest

from app.agent.environment.windows_desktop_environment_adapter import (
    DesktopWindowSnapshot,
)
from app.runtime.execution.window.window_rect import WindowRect
from tools.smoke_windows_desktop_window_activation import (
    _configure_console_output as configure_activation_console,
    _parse_args,
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
        title_must_be_empty=False,
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



def test_activation_smoke_selects_only_a_uniquely_untitled_root_window():
    titled_offer = _window(
        "Okna.exe",
        "Okna - OFR/4522-",
        handle=200,
    )
    untitled_root = _window(
        "Okna.exe",
        None,
        handle=300,
    )

    selected = select_target_window(
        (titled_offer, untitled_root),
        process_name="Okna.exe",
        title_must_be_empty=True,
    )

    assert selected is untitled_root


def test_activation_smoke_rejects_untitled_window_owned_by_other_window():
    owned_dialog = _window(
        "Okna.exe",
        None,
        handle=300,
    )
    owned_dialog = DesktopWindowSnapshot(
        handle=owned_dialog.handle,
        title=owned_dialog.title,
        rect=owned_dialog.rect,
        application=owned_dialog.application,
        root_owner_handle=200,
        is_foreground=owned_dialog.is_foreground,
        is_minimized=owned_dialog.is_minimized,
        is_visible=owned_dialog.is_visible,
    )

    with pytest.raises(
        ValueError,
        match="activation_smoke_target_not_unique: matches=0",
    ):
        select_target_window(
            (owned_dialog,),
            process_name="Okna.exe",
            title_must_be_empty=True,
        )


def test_activation_diagnostics_distinguish_missing_title_from_placeholder(
    capsys,
):
    from tools.smoke_windows_desktop_window_activation import (
        _print_target_diagnostics,
    )

    untitled = _window("Okna.exe", None, handle=200)

    _print_target_diagnostics(
        (untitled,),
        process_name="Okna.exe",
        title_contains=None,
        title_must_be_empty=True,
        foreground_application="Code.exe",
        foreground_title="Visual Studio Code",
    )

    output = capsys.readouterr().out
    assert "Requested title selector: <BRAK TYTUŁU>" in output
    assert "<BRAK TYTUŁU>" in output
    assert "MATCH_CANDIDATE" in output
    assert "Untitled window" not in output
    assert "200" not in output



def test_activation_smoke_supports_diagnose_only_without_activation(monkeypatch):
    import sys

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "smoke_windows_desktop_window_activation.py",
            "--target-process",
            "Okna.exe",
            "--target-title-empty",
            "--diagnose-only",
        ],
    )

    args = _parse_args()

    assert args.target_process == "Okna.exe"
    assert args.target_title_empty is True
    assert args.target_title_contains is None
    assert args.diagnose_only is True



def test_activation_smoke_selects_one_independent_root_window_without_title():
    main_window = _window(
        "Okna.exe",
        "Okna - OFR/4522-",
        handle=100,
    )
    owned_properties = DesktopWindowSnapshot(
        handle=200,
        title="Właściwości dokumentu",
        rect=WindowRect(left=10, top=10, width=869, height=752),
        application="Okna.exe",
        root_owner_handle=100,
        is_foreground=False,
        is_visible=True,
    )
    tiny_owned_window = DesktopWindowSnapshot(
        handle=300,
        title=None,
        rect=WindowRect(left=0, top=0, width=1, height=1),
        application="Okna.exe",
        root_owner_handle=100,
        is_foreground=False,
        is_visible=True,
    )

    selected = select_target_window(
        (main_window, owned_properties, tiny_owned_window),
        process_name="Okna.exe",
        root_window_only=True,
    )

    assert selected is main_window


def test_activation_smoke_refuses_multiple_independent_root_windows():
    windows = (
        _window("Okna.exe", "Okna - Angebot 1", handle=100),
        _window("Okna.exe", "Okna - Angebot 2", handle=200),
    )

    with pytest.raises(
        ValueError,
        match="activation_smoke_target_not_unique: matches=2",
    ):
        select_target_window(
            windows,
            process_name="Okna.exe",
            root_window_only=True,
        )


def test_activation_smoke_requires_exactly_one_identity_selector():
    windows = (_window("Okna.exe", "Okna - Angebot", handle=100),)

    with pytest.raises(ValueError, match="activation_smoke_selectors_required"):
        select_target_window(
            windows,
            process_name="Okna.exe",
        )

    with pytest.raises(ValueError, match="activation_smoke_selectors_required"):
        select_target_window(
            windows,
            process_name="Okna.exe",
            title_contains="Angebot",
            root_window_only=True,
        )



def test_activation_smoke_cli_accepts_root_window_selector(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "smoke_windows_desktop_window_activation.py",
            "--target-process",
            "Okna.exe",
            "--target-root-window",
            "--diagnose-only",
        ],
    )

    args = _parse_args()

    assert args.target_process == "Okna.exe"
    assert args.target_root_window is True
    assert args.target_title_contains is None
    assert args.target_title_empty is False
    assert args.diagnose_only is True
