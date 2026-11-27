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
    assert 'print("NAVIMIND_V2_EXECUTOR_CONNECTED=False")' in data
    assert 'print("NAVIMIND_GUI_LIVE_ENABLED=" + str(live_allowed))' in data
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


def test_discovery_reply_grounded_in_real_local_tool_output():
    answer = workspace.windowhub_discovery_answer((
        "WINDOWHUB_DISCOVERY=FOUND",
        "WINDOWHUB_IS_FOREGROUND=False",
    ))
    assert "w tle" in answer
    assert "tworzenia" in answer
    missing = workspace.windowhub_discovery_answer((
        "WINDOWHUB_DISCOVERY=NOT_FOUND",
    ))
    assert "Nie znalazłem" in missing


def test_no_keyword_dispatch_and_no_find_windowhub_button():
    source = (Path(__file__).resolve().parents[1] / "tools" /
              "navimind_main_workspace.py").read_text(encoding="utf-8")
    assert 'text="Znajdź WindowHub"' not in source
    assert "requested_local_tool" not in source
    assert "self.conversation.submit_current_message(message.message_id)" in source
    launcher = (Path(__file__).resolve().parents[1] / "tools" /
                "run_navimind_shared_control_center.py").read_text(encoding="utf-8")
    assert "read_only_tools=tool_registry" in launcher
    assert '"find_windowhub": ReadOnlyTool(' in launcher


@pytest.mark.parametrize("shift,expected", [
    (False, "send"),
    (True, "newline"),
])
def test_enter_and_shift_enter_actions(shift, expected):
    assert workspace.chat_key_action(shift=shift) == expected


def test_chat_entry_key_handlers_without_tk_window():
    class UI:
        sent = 0
        def _send(self):
            self.sent += 1
    ui = UI()
    enter = type("Key", (), {"state": 0})()
    shift_enter = type("Key", (), {"state": 0x0001})()
    assert workspace.NaviMindMainWorkspace._keyboard_enter(ui, enter) == "break"
    assert ui.sent == 1
    assert workspace.NaviMindMainWorkspace._keyboard_enter(ui, shift_enter) is None
    assert ui.sent == 1
    assert workspace.NaviMindMainWorkspace._keyboard_newline(ui, shift_enter) is None


def test_workspace_styles_and_keys_are_connected():
    source = (Path(__file__).resolve().parents[1] / "tools" /
              "navimind_main_workspace.py").read_text(encoding="utf-8")
    assert 'self.entry.bind("<Return>", self._keyboard_enter)' in source
    assert 'self.entry.bind("<Shift-Return>", self._keyboard_newline)' in source
    assert 'self.entry.bind("<KP_Enter>", self._keyboard_enter)' in source
    assert 'self.entry.bind("<Control-Return>", self._keyboard_send)' in source
    assert "NaviMind" in source and "Inteligentny workspace" in source
    assert "DOKUMENTY KLIENTA" in source


def test_local_pdf_model_context_is_bounded_and_marks_truncation():
    inbox = LocalEnquiryInbox()
    inbox.set_text("Fenster 990 x 920 mm " * 500)
    context = inbox.model_context(max_chars=1200)
    assert len(context) <= 1200
    assert "NIEZAUFANE DANE" in context
    assert "990 x 920" in context
    assert "treść przekracza limit" in context
    assert inbox.status()["transmitted_to_model"] is False


def test_multiple_long_pdfs_all_remain_visible_in_approved_bounded_context():
    from app.agent.runtime.navimind_enquiry_inbox import EnquirySource

    inbox = LocalEnquiryInbox()
    inbox.set_text("DRAFT_BEGIN " + "X" * 9000)
    inbox._sources = [
        EnquirySource("private-customer-one.pdf", "pdf",
                      "FIRST_PDF_WIDTH_990 " + "A" * 9000,
                      3, False, False),
        EnquirySource("private-customer-two.pdf", "pdf",
                      "SECOND_PDF_WIDTH_1400 " + "B" * 9000,
                      2, False, False),
    ]
    context = inbox.model_context(max_chars=1200)
    assert len(context) <= 1200
    assert "DRAFT_BEGIN" in context
    assert "FIRST_PDF_WIDTH_990" in context
    assert "SECOND_PDF_WIDTH_1400" in context
    assert "PDF 1 (stron: 3)" in context
    assert "PDF 2 (stron: 2)" in context
    assert "fragmenty źródeł skrócono" in context
    assert "private-customer-one.pdf" not in context
    assert "private-customer-two.pdf" not in context
    assert inbox.status()["transmitted_to_model"] is False


def test_scanned_pdf_context_never_claims_full_ocr(tmp_path):
    fitz = pytest.importorskip("fitz")
    path = tmp_path / "scan.pdf"
    pdf = fitz.open()
    pdf.new_page()
    pdf.save(str(path))
    pdf.close()
    inbox = LocalEnquiryInbox()
    inbox.add_pdf(path)
    text = inbox.model_context()
    assert "brak tekstu" in text
    assert "ODCZYT NIEPEŁNY" in text
    assert "scan.pdf" not in text


def test_operator_must_confirm_sharing_document_to_ai(monkeypatch):
    from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
    from app.agent.runtime.navimind_mission_chat import MissionChat
    from types import SimpleNamespace
    inbox = LocalEnquiryInbox()
    inbox.set_text("Fenster 990 x 920 mm")
    panel = workspace.NaviMindMainWorkspace.__new__(workspace.NaviMindMainWorkspace)
    chat = MissionChat(document_key="disposable", arbiter=LocalInputArbiter())
    panel.chat = chat
    panel.enquiry = inbox
    class Editor:
        def get(self, start, end):
            return "Fenster 990 x 920 mm"
    panel.enquiry_editor = Editor()
    class StatusLabel:
        text = None
        def configure(self, **kwargs):
            self.text = kwargs.get("text")
    panel.notice = StatusLabel()
    class Conversation:
        approved = None
        submissions = []
        def status(self):
            return SimpleNamespace(provider_connected=True)
        def approve_document_context(self, context, **kwargs):
            self.approved = context
        def revoke_document_context(self):
            self.approved = None
        def submit_current_message(self, message_id):
            self.submissions.append(message_id)
            return True
    conversation = Conversation()
    panel.conversation = conversation
    panel._refresh_messages = lambda: None
    monkeypatch.setattr(workspace.messagebox, "askyesno", lambda *a, **kw: False)
    panel._share_document_with_ai()
    assert conversation.approved is None
    assert conversation.submissions == []
    assert chat.snapshot().messages == ()

    monkeypatch.setattr(workspace.messagebox, "askyesno", lambda *a, **kw: True)
    panel._share_document_with_ai()
    assert "990 x 920" in conversation.approved
    assert len(conversation.submissions) == 1
    assert chat.snapshot().messages[-1].role.value == "human"
    assert "Przeanalizuj" in chat.snapshot().messages[-1].text


def test_workspace_has_document_sharing_and_revocation_buttons():
    source = (Path(__file__).resolve().parents[1] / "tools" /
              "navimind_main_workspace.py").read_text(encoding="utf-8")
    assert 'text="Przeanalizuj dokument w NaviMind"' in source
    assert 'text="Cofnij dostęp AI"' in source
    assert "self.conversation.revoke_document_context()" in source
    assert 'text="Dodaj PDF"' in source
    assert "Polecenia dla NaviMind wpisuj w rozmowie wyżej." in source
