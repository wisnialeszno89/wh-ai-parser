from types import SimpleNamespace

from app.agent.environment import (
    windows_desktop_environment_adapter as module,
)
from app.agent.environment.windows_desktop_environment_adapter import (
    WindowsDesktopEnvironmentAdapter,
)


def test_windows_desktop_observes_active_window(
    monkeypatch,
):
    window = SimpleNamespace(
        title="Visual Studio Code",
        _hWnd=200,
        left=100,
        top=200,
        width=1200,
        height=800,
    )

    monkeypatch.setattr(
        module.gw,
        "getActiveWindow",
        lambda: window,
    )

    adapter = WindowsDesktopEnvironmentAdapter()

    adapter.screenshot_engine = SimpleNamespace(
        capture=lambda rect: SimpleNamespace(
            width=rect.width,
            height=rect.height,
        )
    )

    monkeypatch.setattr(
        WindowsDesktopEnvironmentAdapter,
        "_foreground_window_handle",
        staticmethod(lambda: 200),
    )

    monkeypatch.setattr(
        WindowsDesktopEnvironmentAdapter,
        "_root_owner_window_handle",
        staticmethod(lambda hwnd: 200),
    )

    observation = adapter.observe()

    assert observation.state.active_application == (
        "WindowsDesktop"
    )
    assert observation.state.active_window_title == (
        "Visual Studio Code"
    )
    assert observation.metadata["window_handle"] == 200
    assert observation.metadata["window_focused"] is True

    rect = observation.metadata["window_rect"]

    assert rect.left == 100
    assert rect.top == 200
    assert rect.width == 1200
    assert rect.height == 800


def test_windows_desktop_fails_closed_without_active_window(
    monkeypatch,
):
    monkeypatch.setattr(
        module.gw,
        "getActiveWindow",
        lambda: None,
    )

    adapter = WindowsDesktopEnvironmentAdapter()

    try:
        adapter.observe()
    except RuntimeError as exc:
        assert str(exc) == (
            "No active Windows desktop window is available."
        )
    else:
        raise AssertionError(
            "Expected fail-closed behaviour."
        )
