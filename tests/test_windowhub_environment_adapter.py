from types import SimpleNamespace

from app.agent.environment import windowhub_environment_adapter as module
from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)


def _window(
    title,
    *,
    hwnd,
    left=0,
    top=0,
    width=100,
    height=100,
):
    return SimpleNamespace(
        title=title,
        _hWnd=hwnd,
        left=left,
        top=top,
        width=width,
        height=height,
    )


def test_windowhub_locator_selects_largest_okna_window(monkeypatch):
    windows = (
        _window(
            "Visual Studio Code",
            hwnd=100,
            width=1900,
            height=1100,
        ),
        _window(
            "Okna - OFR/1234",
            hwnd=200,
            width=1200,
            height=800,
        ),
        _window(
            "Okna - OFR/5678",
            hwnd=300,
            width=1900,
            height=1050,
        ),
    )

    monkeypatch.setattr(
        module.gw,
        "getAllWindows",
        lambda: windows,
    )

    selected = WindowHubEnvironmentAdapter._locate_windowhub_window()

    assert selected.title == "Okna - OFR/5678"
    assert selected._hWnd == 300


def test_windowhub_locator_rejects_when_no_windowhub_window_exists(
    monkeypatch,
):
    monkeypatch.setattr(
        module.gw,
        "getAllWindows",
        lambda: (
            _window(
                "Visual Studio Code",
                hwnd=100,
                width=1900,
                height=1100,
            ),
        ),
    )

    try:
        WindowHubEnvironmentAdapter._locate_windowhub_window()
    except RuntimeError as exc:
        assert str(exc) == "WindowHub window not found."
    else:
        raise AssertionError(
            "WindowHub locator must fail closed when no WindowHub window exists."
        )


def test_windowhub_locator_ignores_minimized_candidates(monkeypatch):
    windows = (
        _window(
            "Okna - minimized",
            hwnd=200,
            left=-20000,
            top=-20000,
            width=2000,
            height=1200,
        ),
        _window(
            "Okna - live",
            hwnd=300,
            width=1000,
            height=700,
        ),
    )

    monkeypatch.setattr(
        module.gw,
        "getAllWindows",
        lambda: windows,
    )

    selected = WindowHubEnvironmentAdapter._locate_windowhub_window()

    assert selected.title == "Okna - live"
    assert selected._hWnd == 300


def test_observe_exposes_foreground_owned_dialog_handles(monkeypatch):
    windows = (
        _window(
            "Okna - OFR/1234",
            hwnd=200,
            width=1200,
            height=800,
        ),
    )

    monkeypatch.setattr(
        module.gw,
        "getAllWindows",
        lambda: windows,
    )

    adapter = WindowHubEnvironmentAdapter()
    adapter.screenshot_engine = SimpleNamespace(
        capture=lambda rect: SimpleNamespace(
            width=1200,
            height=800,
        )
    )

    monkeypatch.setattr(
        WindowHubEnvironmentAdapter,
        "_foreground_window_handle",
        staticmethod(lambda: 400),
    )
    monkeypatch.setattr(
        WindowHubEnvironmentAdapter,
        "_root_owner_window_handle",
        staticmethod(lambda hwnd: 200),
    )

    observation = adapter.observe()

    assert observation.metadata["window_handle"] == 200
    assert observation.metadata["foreground_window_handle"] == 400
    assert observation.metadata["foreground_root_owner_handle"] == 200
    assert observation.metadata["window_focused"] is False
