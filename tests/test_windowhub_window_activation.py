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
