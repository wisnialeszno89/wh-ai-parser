"""An approved-source ledger query must never trigger a WindowHub wizard probe."""
import time

from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_local_position_ledger_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool

PROMPT = (
    "NaviMind, sprawdź, czy lokalna ewidencja zawiera dokładnie "
    "dwa okna 1500x1400 i 1300x1200 mm. "
    "Jeśli coś się nie zgadza, podaj konkretną blokadę i nie zgaduj parametrów."
)


class NeverUseModel:
    def reply(self, **kwargs):
        raise AssertionError("approved local ledger lookup must not call model")


def idle(engine):
    deadline = time.monotonic() + 5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not engine.status().active


def test_local_ledger_intent_is_distinct_from_wh_catalogue():
    assert explicit_local_position_ledger_request(PROMPT)
    assert not explicit_local_position_ledger_request(
        "Sprawdź katalogi okuć w kreatorze WindowHub."
    )


def test_approved_source_check_never_queries_windowhub_catalogue():
    calls = []
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    engine = LiveMissionConversation(
        chat, NeverUseModel(),
        read_only_tools={
            "read_approved_enquiry": ReadOnlyTool(
                "read_approved_enquiry", "Local approved source",
                lambda: calls.append("source") or
                "WYKRYTE_POZYCJE=2: S01-P001 1500x1400; S01-P002 1300x1200",
                requires_document_consent=True,
            ),
            "audit_windowhub_catalogues": ReadOnlyTool(
                "audit_windowhub_catalogues", "Catalogues",
                lambda: calls.append("catalogue") or "WRONG",
            ),
        },
    )
    engine.approve_document_context("2 test windows")
    msg = chat.user_message(PROMPT)
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == ["source"]
    assert "WYKRYTE_POZYCJE=2" in chat.snapshot().messages[-1].text
    engine.close()


def test_unapproved_local_source_check_requests_consent_and_no_tools():
    calls = []
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    engine = LiveMissionConversation(
        chat, NeverUseModel(),
        read_only_tools={
            "read_approved_enquiry": ReadOnlyTool(
                "read_approved_enquiry", "Local approved source",
                lambda: calls.append("source") or "PRIVATE",
                requires_document_consent=True,
            ),
        },
    )
    msg = chat.user_message(PROMPT)
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == []
    assert engine.take_pending_document_approval() == (
        msg.mission_revision, msg.message_id,
    )
    engine.close()
