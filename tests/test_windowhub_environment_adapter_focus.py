from types import SimpleNamespace

from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)


def make_adapter(monkeypatch, *, target_handle, foreground_handle, root_owner_handle):
    window = SimpleNamespace(
        title="Okna - OFR/4195-",
        left=0,
        top=0,
        width=1920,
        height=1080,
        _hWnd=target_handle,
    )
    monkeypatch.setattr(
        WindowHubEnvironmentAdapter,
        "_locate_windowhub_window",
        staticmethod(lambda: window),
    )
    monkeypatch.setattr(
        WindowHubEnvironmentAdapter,
        "_foreground_window_handle",
        staticmethod(lambda: foreground_handle),
    )
    monkeypatch.setattr(
        WindowHubEnvironmentAdapter,
        "_root_owner_window_handle",
        staticmethod(lambda _handle: root_owner_handle),
    )

    adapter = WindowHubEnvironmentAdapter()
    adapter.screenshot_engine = SimpleNamespace(
        capture=lambda rect: SimpleNamespace(width=rect.width, height=rect.height)
    )
    return adapter


def test_owned_foreground_dialog_counts_as_windowhub_focused(monkeypatch):
    adapter = make_adapter(
        monkeypatch,
        target_handle=410,
        foreground_handle=990,
        root_owner_handle=410,
    )

    observation = adapter.observe()

    assert observation.metadata["window_focused"] is True
    assert observation.metadata["window_handle"] == 410
    assert observation.metadata["foreground_window_handle"] == 990
    assert observation.metadata["foreground_root_owner_handle"] == 410


def test_unrelated_foreground_window_does_not_count_as_windowhub_focused(monkeypatch):
    adapter = make_adapter(
        monkeypatch,
        target_handle=410,
        foreground_handle=990,
        root_owner_handle=770,
    )

    observation = adapter.observe()

    assert observation.metadata["window_focused"] is False


def test_invalid_window_handle_never_counts_as_focused(monkeypatch):
    adapter = make_adapter(
        monkeypatch,
        target_handle=0,
        foreground_handle=0,
        root_owner_handle=0,
    )

    observation = adapter.observe()

    assert observation.metadata["window_focused"] is False
