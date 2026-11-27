"""Regression tests for user-explicit, consent-gated local enquiry fallback."""
import time

from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_local_enquiry_read_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool


def _idle(engine):
    until = time.monotonic() + 3.5
    while engine.status().active and time.monotonic() < until:
        time.sleep(0.005)
    assert not engine.status().active


def test_exact_polish_prompt_matches_but_status_and_refusal_do_not():
    assert explicit_local_enquiry_read_request(
        "Przeanalizuj lokalne zapytanie klienta, które zostało wczytane "
        "przy uruchomieniu. Podaj liczbę pozycji, wymiary każdego okna."
    )
    assert not explicit_local_enquiry_read_request(
        "Sprawdź, czy lokalne zapytanie klienta istnieje."
    )
    assert not explicit_local_enquiry_read_request(
        "Nie czytaj dokumentu klienta, tylko sprawdź status."
    )
    assert not explicit_local_enquiry_read_request(
        "Przygotuj ofertę w WindowHub bez czytania dokumentu."
    )


class BrokenDecisionProvider:
    def __init__(self):
        self.calls = []

    def reply(self, *, transcript, instructions):
        self.calls.append(transcript)
        if any("[WYNIK ZAUFANEGO LOKALNEGO NARZĘDZIA" in text
               for role, text in transcript):
            return '{"kind":"answer","answer":"Okno 1500 x 1400 mm."}'
        return "To nie jest JSON"


def test_invalid_tool_decision_prompts_for_consent_before_local_read():
    chat = MissionChat(document_key="DISPOSABLE", arbiter=LocalInputArbiter())
    provider = BrokenDecisionProvider()
    executions = []
    engine = LiveMissionConversation(
        chat, provider,
        read_only_tools={
            "read_approved_enquiry": ReadOnlyTool(
                "read_approved_enquiry", "Przeanalizuj lokalne zapytanie",
                lambda: executions.append(1) or "Okno 1500 x 1400 mm",
                requires_document_consent=True, synthesize_result=True,
            ),
        },
        allow_tool_chaining=True,
    )
    message = chat.user_message(
        "Przeanalizuj lokalne zapytanie klienta i podaj wymiary."
    )
    assert engine.submit_current_message(message.message_id)
    _idle(engine)
    assert not executions
    assert engine.take_pending_document_approval() == (
        message.mission_revision, message.message_id,
    )
    assert len(provider.calls) == 2
    assert all("1500 x 1400" not in str(call) for call in provider.calls)
    engine.approve_document_context("Okno 1500 x 1400 mm")
    assert engine.submit_current_message(message.message_id)
    _idle(engine)
    assert executions == [1]
    assert "1500 x 1400" in chat.snapshot().messages[-1].text
    engine.close()
