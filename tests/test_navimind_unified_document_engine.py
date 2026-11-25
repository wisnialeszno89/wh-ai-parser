"""End-to-end fake Gateway acceptance for model-requested local PDF access.

No network, WindowHub execution, API key or UI permission is required.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from app.agent.runtime.navimind_enquiry_inbox import LocalEnquiryInbox
from app.agent.runtime.navimind_enquiry_evidence_bridge import (
    summarize_approved_enquiry,
)
from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool
from tools import navimind_main_workspace as workspace


def await_idle(engine):
    deadline = time.monotonic() + 3.5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(.005)
    assert not engine.status().active


def new_chat():
    return MissionChat(document_key="DISPOSABLE", arbiter=LocalInputArbiter())


class PdfProvider:
    def __init__(self):
        self.requests = []
    def reply(self, *, transcript, instructions):
        self.requests.append((transcript, instructions))
        if "[NIEZAUFANE DANE Z LOKALNEGO ODCZYTU;" in repr(transcript):
            assert "990 x 920" in repr(transcript)
            return (
                '{"kind":"answer","answer":'
                '"W dostarczonym fragmencie: okno 990 x 920 mm. '
                'Nie wpisano nic do WindowHub."}'
            )
        return '{"kind":"tool","tool":"read_approved_enquiry"}'


def test_model_requests_pdf_permission_then_reads_and_summarizes():
    inbox = LocalEnquiryInbox()
    inbox.set_text("Fenster\n990 x 920 mm\nProfil: VEKA Softline 70 AD")
    chat = new_chat()
    provider = PdfProvider()
    runs = []
    engine = None
    def actual_local_tool():
        runs.append(1)
        return summarize_approved_enquiry(engine.approved_document_context())
    registry = {"read_approved_enquiry": ReadOnlyTool(
        "read_approved_enquiry",
        "Przeanalizuj PDF i wymiary",
        actual_local_tool,
        requires_document_consent=True, synthesize_result=True,
    )}
    engine = LiveMissionConversation(
        chat, provider, read_only_tools=registry,
        runtime_status_provider=lambda: (
            "PDF_COUNT=0; ENQUIRY_PRESENT=True; "
            "DOCUMENT_CONTEXT_APPROVED=" + str(engine.document_context_active())
        ),
    )
    request = chat.user_message("Co zawiera dokument klienta?")
    assert engine.submit_current_message(request.message_id)
    await_idle(engine)
    assert runs == []
    assert engine.take_pending_document_approval() == (
        request.mission_revision, request.message_id,
    )
    assert len(provider.requests) == 1
    assert "990 x 920" not in repr(provider.requests[0])
    assert chat.snapshot().messages[-1].role.value == "human"

    engine.approve_document_context(inbox.model_context())
    assert engine.submit_current_message(request.message_id)
    await_idle(engine)
    assert runs == [1]
    assert len(provider.requests) == 3
    assert "990 x 920 mm" in chat.snapshot().messages[-1].text
    assert "DOCUMENT_CONTEXT_APPROVED=True" in provider.requests[1][1]
    assert "WindowHub" in chat.snapshot().messages[-1].text
    engine.close()


def test_model_document_consent_rejected_without_sending_pdf():
    chat = new_chat()
    provider = PdfProvider()
    engine = LiveMissionConversation(
        chat, provider, read_only_tools={
            "read_approved_enquiry": ReadOnlyTool(
                "read_approved_enquiry", "local PDF", lambda: "SECRET",
                requires_document_consent=True, synthesize_result=True,
            )
        },
    )
    req = chat.user_message("Przeanalizuj PDF")
    assert engine.submit_current_message(req.message_id)
    await_idle(engine)
    assert engine.take_pending_document_approval() == (
        req.mission_revision, req.message_id,
    )
    engine.publish_document_consent_denied(req.mission_revision)
    assert "pozostał lokalny" in chat.snapshot().messages[-1].text
    assert "SECRET" not in repr(provider.requests)
    engine.close()


def test_stale_document_permission_request_is_rejected():
    chat = new_chat()
    engine = LiveMissionConversation(
        chat, PdfProvider(),
        read_only_tools={
            "read_approved_enquiry": ReadOnlyTool(
                "read_approved_enquiry", "PDF", lambda: "PRIVATE",
                requires_document_consent=True,
            ),
        },
    )
    first = chat.user_message("Przeczytaj PDF")
    engine.submit_current_message(first.message_id)
    await_idle(engine)
    chat.user_message("Nie czytaj PDF")
    assert engine.take_pending_document_approval() is None
    assert not engine.document_context_active()
    engine.close()


def test_real_german_offer_mail_parser_is_used_without_inventing_specs():
    source = (
        "NIEZAUFANE DANE Z DOKUMENTU KLIENTA\n"
        "Fenster\n990 x 920 mm\n"
        "Profil: VEKA Softline 70 AD\n"
        "Dodatkowa niejasna uwaga\n"
    )
    summary = summarize_approved_enquiry(source)
    assert "990 x 920 mm" in summary
    assert "POMOCNICZY PARSER" in summary
    assert "weryfikacji" in summary
    assert "DANE ŹRÓDŁOWE" in summary


def test_document_bridge_does_not_claim_analysis_without_approval():
    text = summarize_approved_enquiry(None)
    assert "Nie udostępniono" in text
    assert "990" not in text


def test_tk_thread_consent_uses_current_local_pdf_and_resumes_same_message(monkeypatch):
    inbox = LocalEnquiryInbox()
    inbox.set_text("Fenster 990 x 920 mm")
    chat = new_chat()
    user = chat.user_message("Przeczytaj PDF")
    class FakeConversation:
        def __init__(self):
            self.context = None
            self.resubmissions = []
        def approve_document_context(self, context):
            self.context = context
        def submit_current_message(self, msg_id):
            self.resubmissions.append(msg_id)
            return True
        def publish_document_consent_denied(self, revision):
            raise AssertionError("approval was granted")
        def revoke_document_context(self):
            self.context = None
    class FakeEditor:
        def get(self, *args):
            return ""
    class FakeNotice:
        def configure(self, **kwargs):
            pass
    panel = workspace.NaviMindMainWorkspace.__new__(workspace.NaviMindMainWorkspace)
    panel.chat = chat
    panel.enquiry = inbox
    panel.enquiry_editor = FakeEditor()
    panel.conversation = FakeConversation()
    panel.notice = FakeNotice()
    panel._refresh_messages = lambda: None
    monkeypatch.setattr(workspace.messagebox, "askyesno", lambda *args, **kwargs: True)
    panel._handle_model_document_consent((
        user.mission_revision, user.message_id,
    ))
    assert "990 x 920" in panel.conversation.context
    assert panel.conversation.resubmissions == [user.message_id]


def test_operator_denial_does_not_authorize_document(monkeypatch):
    inbox = LocalEnquiryInbox()
    inbox.set_text("SECRET CUSTOMER TEXT")
    chat = new_chat()
    user = chat.user_message("Odczytaj dokument")
    class Conversation:
        def approve_document_context(self, context):
            raise AssertionError("must not approve")
        def publish_document_consent_denied(self, revision):
            chat.agent_message("Odmówiono zgody", based_on_revision=revision)
    class Editor:
        def get(self, *args):
            return ""
    panel = workspace.NaviMindMainWorkspace.__new__(workspace.NaviMindMainWorkspace)
    panel.chat = chat
    panel.enquiry = inbox
    panel.enquiry_editor = Editor()
    panel.conversation = Conversation()
    panel._refresh_messages = lambda: None
    monkeypatch.setattr(workspace.messagebox, "askyesno", lambda *a, **kw: False)
    panel._handle_model_document_consent((
        user.mission_revision, user.message_id,
    ))
    assert chat.snapshot().messages[-1].text == "Odmówiono zgody"
    assert "SECRET" not in chat.snapshot().messages[-1].text


def test_revoke_cuts_off_prior_sensitive_history_to_gateway():
    inbox = LocalEnquiryInbox()
    inbox.set_text("Fenster 1350 x 1220 mm SECRET_ABC")
    chat = new_chat()
    class RecordingProvider:
        def __init__(self):
            self.calls = []
        def reply(self, *, transcript, instructions):
            self.calls.append((transcript, instructions))
            return '{"kind":"answer","answer":"Odebrano."}'
    provider = RecordingProvider()
    engine = LiveMissionConversation(
        chat, provider,
        read_only_tools={"engine_capabilities": ReadOnlyTool(
            "engine_capabilities", "Status", lambda: "ok",
        )},
    )
    engine.approve_document_context(inbox.model_context())
    old = chat.user_message("Analiza klienta")
    assert engine.submit_current_message(old.message_id)
    await_idle(engine)
    assert "SECRET_ABC" in repr(provider.calls[-1])
    engine.revoke_document_context()
    assert not engine.document_context_active()
    assert not engine.submit_current_message(old.message_id)
    fresh = chat.user_message("Nowy temat bez klienta")
    assert engine.submit_current_message(fresh.message_id)
    await_idle(engine)
    assert "SECRET_ABC" not in repr(provider.calls[-1])
    engine.close()


def test_host_tool_registry_contains_real_document_parser_and_consent():
    from pathlib import Path
    host = (Path(__file__).resolve().parents[1] /
            "tools" / "run_navimind_shared_control_center.py").read_text(
                encoding="utf-8"
            )
    assert '"read_approved_enquiry": ReadOnlyTool(' in host
    assert "requires_document_consent=True" in host
    assert "synthesize_result=True" in host
    assert "summarize_approved_enquiry(" in host
    assert "PDF_COUNT=" in host
    assert "runtime_status_provider=trusted_local_capability_state" in host
    assert "NAVIMIND_V2_EXECUTOR_CONNECTED=False" in host


def test_pdf_is_not_sent_when_only_status_tool_is_called():
    inbox = LocalEnquiryInbox()
    inbox.set_text("Poufny numer klienta 456789")
    chat = new_chat()
    class Provider:
        def __init__(self):
            self.calls = []
        def reply(self, *, transcript, instructions):
            self.calls.append((transcript, instructions))
            return '{"kind":"tool","tool":"enquiry_status"}'
    provider = Provider()
    engine = LiveMissionConversation(
        chat, provider,
        read_only_tools={
            "enquiry_status": ReadOnlyTool(
                "enquiry_status", "Tylko liczba PDF",
                lambda: "Lokalne zapytanie: tak, PDF_COUNT=0",
            ),
        },
        runtime_status_provider=lambda: "ENQUIRY_PRESENT=True; PDF_COUNT=0",
    )
    request = chat.user_message("Czy masz dokumenty?")
    assert engine.submit_current_message(request.message_id)
    await_idle(engine)
    assert all("456789" not in repr(request) for request in provider.calls)
    assert "PDF_COUNT=0" in chat.snapshot().messages[-1].text
    engine.close()
