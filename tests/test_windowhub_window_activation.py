import os

from app.agent.runtime.windowhub_window_activation import activate_windowhub_wizard


def test_activation_requires_live_authorization(monkeypatch):
    monkeypatch.delenv('WH_REAL_WINDOWHUB', raising=False)
    monkeypatch.delenv('COMPUTER_USE_LIVE', raising=False)
    ok, reason = activate_windowhub_wizard()
    assert ok is False
    assert reason


def test_activation_never_succeeds_without_explicit_flags(monkeypatch):
    monkeypatch.setenv('WH_REAL_WINDOWHUB', '1')
    monkeypatch.delenv('COMPUTER_USE_LIVE', raising=False)
    ok, reason = activate_windowhub_wizard()
    assert ok is False
    assert reason


def test_focus_can_transfer_via_attached_input_queues(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    import ctypes
    from app.agent.runtime.windowhub_window_activation import _focus_existing_window

    foreground = [100]
    attached = []

    def attach(current, other, enabled):
        attached.append((other, bool(enabled)))
        return True

    def set_foreground(hwnd):
        if len([item for item in attached if item[1]]) == 2:
            foreground[0] = hwnd
        return 1

    user32 = SimpleNamespace(
        GetForegroundWindow=Mock(side_effect=lambda: foreground[0]),
        ShowWindow=Mock(return_value=1),
        SetForegroundWindow=Mock(side_effect=set_foreground),
        GetWindowThreadProcessId=Mock(side_effect=lambda hwnd, _: {100: 10, 200: 20}[hwnd]),
        AttachThreadInput=Mock(side_effect=attach),
        BringWindowToTop=Mock(return_value=1),
    )
    kernel32 = SimpleNamespace(GetCurrentThreadId=Mock(return_value=30))
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=kernel32), raising=False)
    assert _focus_existing_window(user32, 200) is True
    assert foreground[0] == 200
    assert attached == [(10, True), (20, True), (20, False), (10, False)]


def test_focus_does_not_send_input_if_target_already_active(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    import ctypes
    from app.agent.runtime.windowhub_window_activation import _focus_existing_window

    user32 = SimpleNamespace(
        GetForegroundWindow=Mock(return_value=200),
        ShowWindow=Mock(),
        SetForegroundWindow=Mock(),
    )
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(), raising=False)
    assert _focus_existing_window(user32, 200) is True
    user32.ShowWindow.assert_not_called()
    user32.SetForegroundWindow.assert_not_called()
