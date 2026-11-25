"""Background UIA reader: no focus switch, no input, bounded structural metadata."""
from types import SimpleNamespace

from app.agent.runtime.navimind_background_windowhub_reader import (
    inspect_windowhub_background, safe_stage,
)


def window(*, process="C:/Winkhaus/Okna.exe", title="Okna - Start1",
           handle=123, foreground=False, minimized=False):
    return SimpleNamespace(
        application=process, title=title, handle=handle,
        is_visible=True, is_minimized=minimized,
        is_foreground=foreground,
    )


class Root:
    def __init__(self, title, children):
        self.title, self.children = title, children
    def window_text(self):
        return self.title
    def descendants(self, *, depth):
        assert depth == 3
        return self.children


class Desktop:
    def __init__(self, roots):
        self.roots = roots
        self.calls = []
    def window(self, *, handle):
        self.calls.append(handle)
        return SimpleNamespace(wrapper_object=lambda: self.roots[handle])


def child(control_type, visible=True):
    return SimpleNamespace(element_info=SimpleNamespace(
        control_type=control_type, visible=visible,
    ))


def test_background_stage_detection_without_window_titles():
    assert safe_stage("Okna - OFR/1234- ACME SECRET") == "offer_document"
    assert safe_stage("Okna - Start1") == "start"
    assert safe_stage("Okna - wrażliwy klient") == "unmapped"


def test_inspects_background_window_without_focus_or_mouse():
    target = window(title="Okna - OFR/1234- ACME SECRET", foreground=False)
    desktop = Desktop({
        target.handle: Root(target.title, [
            child("Button"), child("Edit"), child("Text"),
        ]),
    })
    reply = inspect_windowhub_background(
        inventory=[target], desktop_factory=lambda: desktop,
    )
    assert desktop.calls == [123]
    assert "bez przełączania" in reply
    assert "offer_document" in reply
    assert "kontrolki interaktywne (ograniczona głębokość): 2" in reply
    assert "ACME" not in reply and "1234" not in reply


def test_ignores_foreground_browser_and_minimized_wh():
    minimized = window(minimized=True)
    foreign = window(process="firefox.exe", title="private Facebook", foreground=True)
    output = inspect_windowhub_background(
        inventory=[foreign, minimized],
        desktop_factory=lambda: (_ for _ in ()).throw(AssertionError()),
    )
    assert "Nie znalazłem niezminimalizowanego" in output


def test_multiple_windowhub_windows_does_not_leak_customer_titles():
    first = window(title="Okna - Start1", handle=51)
    second = window(title="Okna - OFR/999- SECRET", handle=52)
    desktop = Desktop({
        51: Root(first.title, [child("Button")]),
        52: Root(second.title, [child("Button")]),
    })
    output = inspect_windowhub_background(
        inventory=[first, second], desktop_factory=lambda: desktop,
    )
    assert "multiple_windows" in output
    assert "sprawdzone okna: 2" in output
    assert "999" not in output and "SECRET" not in output


def test_wrong_title_refuses_to_claim_read_success():
    target = window(title="Okna - Start1")
    desktop = Desktop({
        123: Root("Okna - changed customer", [child("Button")]),
    })
    output = inspect_windowhub_background(
        inventory=[target], desktop_factory=lambda: desktop,
    )
    assert "nie potwierdziłem" in output


def test_background_reader_fails_closed_if_uia_access_raises():
    target = window(title="Okna - Start1")
    class BrokenDesktop:
        def window(self, *, handle):
            raise RuntimeError("private customer secret 123")
    output = inspect_windowhub_background(
        inventory=[target], desktop_factory=BrokenDesktop,
    )
    assert "Nie udało się" in output
    assert "secret" not in output


def test_host_registers_background_inspector_as_ai_tool():
    from pathlib import Path
    text = (
        Path(__file__).resolve().parents[1] /
        "tools" / "run_navimind_shared_control_center.py"
    ).read_text(encoding="utf-8")
    assert '"inspect_windowhub": ReadOnlyTool(' in text
    assert "inspect_windowhub_background()" in text
    assert "pythoncom.CoInitialize()" in text
    assert 'print("NAVIMIND_V2_EXECUTOR_CONNECTED=" + str(live_allowed))' in text
