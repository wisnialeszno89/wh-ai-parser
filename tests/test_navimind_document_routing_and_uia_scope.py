"""Regression: equivalent approved-document requests and ambiguous UIA status."""
import time
from types import SimpleNamespace
from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_local_enquiry_read_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool
from app.agent.runtime.navimind_background_windowhub_reader import inspect_windowhub_background


class Provider:
    def reply(self, *, transcript, instructions):
        if any("WYNIK ZAUFANEGO LOKALNEGO NARZĘDZIA" in value
               for _, value in transcript):
            return '{"kind":"answer","answer":"Pozycje: 2; 1500x1400 i 1300x1200."}'
        return '{"kind":"answer","answer":"Nie mam zatwierdzonego dokumentu."}'


def idle(engine):
    end = time.monotonic() + 5
    while engine.status().active and time.monotonic() < end:
        time.sleep(0.01)
    assert not engine.status().active


def test_two_common_phrasings_choose_same_local_document_reader():
    prompts = (
        "Przeanalizuj zatwierdzone zapytanie klienta. Podaj dwie pozycje.",
        "Przeanalizuj udostępnione zapytanie klienta/PDF i wypisz wymiary.",
    )
    assert all(explicit_local_enquiry_read_request(p) for p in prompts)
    for prompt in prompts:
        chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
        calls = []
        engine = LiveMissionConversation(
            chat, Provider(),
            read_only_tools={
                "read_approved_enquiry": ReadOnlyTool(
                    "read_approved_enquiry", "Approved enquiry",
                    lambda: calls.append(True) or "2 okna: 1500x1400, 1300x1200",
                    requires_document_consent=True,
                    synthesize_result=True,
                ),
            },
            allow_tool_chaining=True,
        )
        engine.approve_document_context("2 okna: 1500x1400, 1300x1200")
        msg = chat.user_message(prompt)
        assert engine.submit_current_message(msg.message_id)
        idle(engine)
        assert calls == [True]
        assert "Pozycje: 2" in chat.snapshot().messages[-1].text
        engine.close()


def test_unapproved_document_is_not_read_or_sent_automatically():
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    calls = []
    engine = LiveMissionConversation(
        chat, Provider(),
        read_only_tools={
            "read_approved_enquiry": ReadOnlyTool(
                "read_approved_enquiry", "Approved enquiry",
                lambda: calls.append(True) or "SECRET_CUSTOMER_DATA",
                requires_document_consent=True,
            ),
        },
        allow_tool_chaining=True,
    )
    msg = chat.user_message("Przeanalizuj zatwierdzone zapytanie klienta.")
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == []
    assert engine.take_pending_document_approval() == (
        msg.mission_revision, msg.message_id,
    )
    engine.close()


def test_multiple_window_uia_reader_reports_ambiguous_scope_without_titles():
    class Root:
        def __init__(self, title):
            self.title = title
        def window_text(self):
            return self.title
        def descendants(self, *, depth):
            return []

    roots = {11:Root("Okna - Start1"), 12:Root("Okna - OFR/123 PRIVATE")}
    class Desktop:
        def window(self, *, handle):
            return SimpleNamespace(wrapper_object=lambda: roots[handle])

    windows = [
        SimpleNamespace(application="Okna.exe", is_visible=True,
                        is_minimized=False, handle=key, title=root.title)
        for key,root in roots.items()
    ]
    result = inspect_windowhub_background(
        inventory=windows, desktop_factory=Desktop,
    )
    assert "multiple_windows" in result
    assert "nie potrafię" in result
    assert "właściwego dokumentu" in result
    assert "PRIVATE" not in result
    assert "123" not in result
