"""Safe WindowHub inventory returns only classified states, not sensitive data."""
from types import SimpleNamespace
from tools.diagnose_windowhub_open_windows import safe_window_summary


def win(handle, title, owner=10, foreground=False, app="Okna.exe"):
    return SimpleNamespace(
        handle=handle, title=title, root_owner_handle=owner,
        is_foreground=foreground, is_visible=True, is_minimized=False,
        application=app,
    )


def test_two_windows_are_classified_without_leaking_customer_title():
    inventory = [
        win(10, "Właściwości dokumentu", foreground=True),
        win(20, "Klient Top Trans Artur Janik 12345"),
        win(30, "Notepad secret", app="notepad.exe"),
    ]
    summary = safe_window_summary(inventory, foreground_handle=10)
    assert len(summary) == 2
    assert summary[0]["stage"] == "document_properties"
    assert summary[0]["foreground"] is True
    assert summary[1]["foreground"] is False
    assert summary[1]["same_root_owner_as_first"] is True
    assert "Top Trans" not in str(summary)
    assert "12345" not in str(summary)


def test_missing_or_different_root_owner_is_not_assumed_related():
    inventory = [
        win(10, "Właściwości dokumentu", owner=11),
        win(20, "Zakładanie nowego klienta", owner=22),
    ]
    assert safe_window_summary(inventory)[1]["same_root_owner_as_first"] is False


def test_non_windowhub_and_minimized_windows_excluded():
    a = win(10, "Okna - Start1")
    b = win(20, "Okna - Start1", app="browser.exe")
    c = win(30, "Okna - Start1")
    c.is_minimized = True
    result = safe_window_summary([a, b, c])
    assert len(result) == 1
    assert result[0]["stage"] == "start"
