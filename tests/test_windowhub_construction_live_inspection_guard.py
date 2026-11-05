"""Guard tests: construction observation cannot run against arbitrary windows."""
from tools import inspect_windowhub_construction_state_live as inspector


def test_refuses_without_explicit_focus_authorization(monkeypatch):
    monkeypatch.setattr(inspector.os, "name", "nt")
    monkeypatch.delenv("WH_REAL_WINDOWHUB", raising=False)
    monkeypatch.delenv("COMPUTER_USE_LIVE", raising=False)
    monkeypatch.setattr(
        inspector, "activate_unique_windowhub_offer_document",
        lambda: (_ for _ in ()).throw(AssertionError("activation must not run")),
    )
    assert inspector.main() == 2


def test_refuses_multiple_or_missing_offer_documents(monkeypatch):
    monkeypatch.setattr(inspector.os, "name", "nt")
    monkeypatch.setenv("WH_REAL_WINDOWHUB", "1")
    monkeypatch.setenv("COMPUTER_USE_LIVE", "1")
    monkeypatch.setattr(
        inspector, "activate_unique_windowhub_offer_document",
        lambda: (False, "Expected exactly one visible Okna.exe offer document; found 2"),
    )
    monkeypatch.setattr(
        inspector, "create_windows_desktop_agent_control_loop",
        lambda: (_ for _ in ()).throw(AssertionError("no observations after refused focus")),
    )
    assert inspector.main() == 4
