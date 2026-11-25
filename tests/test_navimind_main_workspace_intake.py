"""Offline acceptance of the local customer request and dictation handoff."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

from app.agent.runtime.navimind_enquiry_inbox import (
    EnquiryInputError, LocalEnquiryInbox, extract_local_pdf, validate_pasted_enquiry,
)
from tools import navimind_main_workspace as workspace


def test_long_multilingual_email_is_preserved_in_local_session():
    inbox = LocalEnquiryInbox()
    email = (
        "Wir möchten im Zuge unserer Sanierung um ein Angebot bitten.\n"
        "EG 1x Stulpfenster 165x150 cm; OG 1x Balkontür 120x210 cm.\n"
        "RC 2 und Wiener Sprossen, Rollläden, iSFP.\n"
    ) * 80
    inbox.set_text(email)
    assert inbox.pasted_text == email.strip()
    assert inbox.status()["has_enquiry"]
    assert inbox.status()["transmitted_to_model"] is False
    assert inbox.status()["persisted"] is False
    assert inbox.status()["windowhub_actions"] == 0
    assert "Stulpfenster" in inbox.preview()


def test_empty_or_oversized_enquiry_is_rejected_without_replacing_existing():
    inbox = LocalEnquiryInbox()
    inbox.set_text("Istniejące zapytanie")
    with pytest.raises(EnquiryInputError, match="empty_enquiry"):
        inbox.set_text(" ")
    with pytest.raises(EnquiryInputError, match="enquiry_exceeds_text_limit"):
        inbox.set_text("X" * 100001)
    assert inbox.pasted_text == "Istniejące zapytanie"


def test_preview_truncation_is_disclosed():
    inbox = LocalEnquiryInbox()
    inbox.set_text("A" * 3000)
    preview = inbox.preview(limit=30)
    assert "Podgląd skrócony" in preview
    assert len(inbox.pasted_text) == 3000


def test_rejects_wrong_extension_and_missing_pdf(tmp_path):
    file = tmp_path / "customer.txt"
    file.write_text("test")
    with pytest.raises(EnquiryInputError, match="pdf_only"):
        extract_local_pdf(file)
    with pytest.raises(EnquiryInputError, match="pdf_not_found"):
        extract_local_pdf(tmp_path / "absent.pdf")


def test_rejects_oversized_pdf_before_attempting_to_parse(tmp_path):
    pdf = tmp_path / "too-large.pdf"
    with open(pdf, "wb") as handle:
        handle.truncate(15 * 1024 * 1024 + 1)
    with pytest.raises(EnquiryInputError, match="pdf_too_large"):
        extract_local_pdf(pdf)


def test_real_text_pdf_is_extracted_locally(tmp_path):
    fitz = pytest.importorskip("fitz")
    file = tmp_path / "angebot.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Fenster 165 x 150 cm, RC2")
    doc.save(str(file))
    doc.close()
    inbox = LocalEnquiryInbox()
    source = inbox.add_pdf(file)
    assert "Fenster" in source.text
    assert source.page_count == 1
    assert not source.truncated
    assert not source.needs_ocr
    assert inbox.status()["pdf_count"] == 1
    assert inbox.status()["transmitted_to_model"] is False


def test_scanned_pdf_is_flagged_not_misrepresented_as_read(tmp_path):
    fitz = pytest.importorskip("fitz")
    file = tmp_path / "skan.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(file))
    doc.close()
    source = extract_local_pdf(file)
    assert source.needs_ocr
    assert source.text == ""
    assert "no_extractable_text" in source.warnings


def test_multi_page_pdf_limit_is_explicit(tmp_path):
    fitz = pytest.importorskip("fitz")
    file = tmp_path / "many.pdf"
    doc = fitz.open()
    for _ in range(41):
        page = doc.new_page()
        page.insert_text((72, 72), "Angebot Fenster")
    doc.save(str(file))
    doc.close()
    source = extract_local_pdf(file)
    assert source.page_count == 41
    assert source.truncated
    assert "partial_pdf_extraction" in source.warnings
    assert source.text.count("Angebot") == 40


def test_windows_dictation_requires_explicit_click_and_is_not_background(monkeypatch):
    class Entry:
        focused = False
        def focus_set(self):
            self.focused = True

    e = Entry()
    calls = []
    monkeypatch.setattr(workspace, "windows_dictation_available", lambda: True)
    assert workspace.start_windows_dictation(e, hotkey=lambda: calls.append("win+h"))
    assert e.focused and calls == ["win+h"]


def test_dictation_disabled_outside_windows(monkeypatch):
    class Entry:
        def focus_set(self):
            raise AssertionError("non-Windows must not focus microphone entry")
    monkeypatch.setattr(workspace, "windows_dictation_available", lambda: False)
    assert workspace.start_windows_dictation(Entry()) is False


def test_host_launcher_mounts_main_workspace_not_detached_chat():
    source = Path(__file__).resolve().parents[1] / "tools" / "run_navimind_shared_control_center.py"
    data = source.read_text(encoding="utf-8")
    assert "panel.mount_main_workspace(" in data
    assert "NaviMindChatWindow(" not in data
    assert "NAVIMIND_V2_EXECUTOR_CONNECTED=False" in data
    assert "NAVIMIND_GUI_INPUT_EXECUTED=False" in data


@pytest.mark.parametrize("content,expected", [
    ("", "empty"),
    ("   ", "empty"),
    ("Zrób wycenę, a jeśli czegoś nie wiesz — zapytaj.", "chat"),
    ("X" * 4000, "chat"),
    ("X" * 4001, "long_enquiry"),
    ("Wir möchten Fenster anbieten.\\n" * 300, "long_enquiry"),
])
def test_chat_input_is_classified_before_mission_chat_limit(content, expected):
    assert workspace.chat_intake_decision(content) == expected


def test_chat_limit_does_not_silently_truncate_customer_enquiry():
    content = "Reihenmittelhaus: Fenster, Türen, Rollläden. " * 110
    assert len(content) > 4000
    assert workspace.chat_intake_decision(content) == "long_enquiry"
    inbox = LocalEnquiryInbox()
    inbox.set_text(content)
    assert inbox.pasted_text == content.strip()
    assert inbox.status()["transmitted_to_model"] is False


def test_unconfigured_provider_warning_is_visible_in_workspace_source():
    source = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "navimind_main_workspace.py"
    ).read_text(encoding="utf-8")
    assert "MODEL AI: NIEPODŁĄCZONY" in source
    assert "Model AI nie jest podłączony" in source
    assert "messagebox.askyesno(" in source


@pytest.mark.parametrize("code,contains", [
    ("chat_authentication_failed_401", "401"),
    ("chat_gateway_credits_or_budget_402", "402"),
    ("chat_gateway_access_denied_403", "403"),
    ("chat_gateway_rate_limited_429", "429"),
    ("chat_transport_unavailable", "sieć"),
])
def test_chat_error_message_is_actionable_and_short(code, contains):
    text = workspace.friendly_chat_error(code)
    assert contains in text
    assert len(text) < 180


def test_arbitrary_exception_message_is_not_displayed():
    assert "supersecret" not in workspace.friendly_chat_error(
        "sensitive-bad-server-exception-supersecret"
    )


@pytest.mark.parametrize("fraction,should_follow", [
    (1.0, True),
    (0.999, True),
    (0.975, True),
    (0.969, False),
    (0.5, False),
    (0.0, False),
])
def test_chat_history_follow_only_if_user_is_near_bottom(fraction, should_follow):
    assert workspace.chat_view_near_bottom(fraction) is should_follow


@pytest.mark.parametrize("wheel_delta,lines", [
    (120, -1), (-120, 1), (240, -2), (-240, 2), (0, 0),
])
def test_chat_scroll_wheel_direction(wheel_delta, lines):
    assert workspace.scroll_history_lines(wheel_delta) == lines


def test_main_workspace_has_history_scrollbar_and_jump_button():
    source = (
        Path(__file__).resolve().parents[1]
        / "tools" / "navimind_main_workspace.py"
    ).read_text(encoding="utf-8")
    assert 'self.history_scrollbar = tk.Scrollbar(' in source
    assert 'yscrollcommand=self.history_scrollbar.set' in source
    assert 'self.history_scrollbar.configure(command=self.history.yview)' in source
    assert 'self.history.bind("<MouseWheel>", self._history_mousewheel)' in source
    assert 'text="↓ Najnowsze"' in source
    assert "if stay_at_bottom:" in source
    assert "scrollbar.configure(command=area.yview)" in source


def test_workspace_discovery_reports_background_without_stealing_focus():
    from queue import Queue
    from types import SimpleNamespace
    panel = workspace.NaviMindMainWorkspace.__new__(workspace.NaviMindMainWorkspace)
    class Status:
        def __init__(self):
            self.message = None
        def configure(self, **kwargs):
            self.message = kwargs.get("text", self.message)
    panel.discovery_status = Status()
    panel.discovery_button = Status()
    panel.discover_windowhub = lambda: ()
    panel._discovery_queue = Queue()
    panel._discovery_active = True
    panel._discovery_queue.put((
        "WINDOWHUB_DISCOVERY=FOUND",
        "WINDOWHUB_IS_FOREGROUND=False",
        "WINDOWHUB_NATIVE_ACTIONS=0",
    ))
    panel._poll_discovery()
    assert panel.discovery_status.message == "WindowHub znaleziony • w tle"
    assert panel._discovery_active is False


def test_discovery_button_exists_but_not_an_input_authority():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / "tools" /
            "navimind_main_workspace.py").read_text(encoding="utf-8")
    assert 'text="Znajdź WindowHub"' in text
    assert 'Thread(target=worker, daemon=True).start()' in text
    assert 'self._poll_discovery()' in text
    assert 'discover_windowhub_read_only' in (
        Path(__file__).resolve().parents[1] / "tools" /
        "run_navimind_shared_control_center.py"
    ).read_text(encoding="utf-8")
