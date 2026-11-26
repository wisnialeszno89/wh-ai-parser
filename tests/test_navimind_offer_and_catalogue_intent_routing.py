"""Regression: explicit offer intent and catalogue comparisons use local host."""
import time

from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_catalogue_evidence_comparison_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool


def idle(engine):
    deadline = time.monotonic() + 5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not engine.status().active


class NeverUseModel:
    def reply(self, **kwargs):
        raise AssertionError("explicit safe local intent must bypass generic LLM")


def test_offer_request_uses_trusted_coordinator_even_without_model():
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    calls = []
    engine = LiveMissionConversation(
        chat, NeverUseModel(),
        read_only_tools={
            "prepare_windowhub_work": ReadOnlyTool(
                "prepare_windowhub_work", "Safe local planner",
                lambda: calls.append("planner") or
                "Misja przyjęta do planowania; zero kliknięć.",
            ),
            "document_sharing_help": ReadOnlyTool(
                "document_sharing_help", "Document help",
                lambda: calls.append("help") or "WRONG",
            ),
        },
        allow_tool_chaining=True,
    )
    msg = chat.user_message(
        "Przygotuj nową niezapisaną ofertę dla Top Trans z dwóch pozycji. "
        "Sprawdź Start1 i zaproponuj następny krok. Nie klikaj."
    )
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == ["planner"]
    assert "zero kliknięć" in chat.snapshot().messages[-1].text
    engine.close()


def test_catalogue_comparison_reports_unverified_products_without_model():
    prompt = (
        "Wyjaśnij, czy możemy już potwierdzić dostępność VEKA Perfectline, "
        "kolorów, szklenia i okuć w katalogu WindowHub. "
        "Oddziel parametry odczytane z PDF od faktycznie zweryfikowanych "
        "w programie. Nie klikaj."
    )
    assert explicit_catalogue_evidence_comparison_request(prompt)
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    calls = []
    engine = LiveMissionConversation(
        chat, NeverUseModel(),
        read_only_tools={
            "audit_windowhub_catalogues": ReadOnlyTool(
                "audit_windowhub_catalogues", "Read-only UIA catalog scope",
                lambda: calls.append("audit") or
                "KATALOG_WH_STATUS=catalogue_wizard_not_found",
            ),
        },
        allow_tool_chaining=True,
    )
    msg = chat.user_message(prompt)
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == ["audit"]
    answer = chat.snapshot().messages[-1].text
    assert "Nie potwierdzono dostępności" in answer
    assert "catalogue_wizard_not_found" in answer
    assert "Bez kliknięć" in answer
    engine.close()


def test_unrelated_question_not_catalogue_comparison():
    assert not explicit_catalogue_evidence_comparison_request(
        "Otwórz listę okuć w WindowHub."
    )
    assert not explicit_catalogue_evidence_comparison_request(
        "Sprawdź lokalną ewidencję pozycji z PDF."
    )

def test_status_of_last_mission_deterministically_uses_host_not_model():
    from app.agent.runtime.navimind_live_conversation import (
        explicit_local_mission_status_request,
    )
    prompt = (
        "Podaj faktyczny status ostatniej misji V2, jej blokadę lub "
        "przygotowany krok i liczbę zweryfikowanych czynności w WindowHub. "
        "Nie wykonuj akcji."
    )
    assert explicit_local_mission_status_request(prompt)
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    calls = []
    engine = LiveMissionConversation(
        chat, NeverUseModel(),
        read_only_tools={
            "mission_status": ReadOnlyTool(
                "mission_status", "Host verified mission state",
                lambda: calls.append("host") or
                "Misja V2: brak przyjętej misji w bieżącej sesji.",
            ),
        },
    )
    msg = chat.user_message(prompt)
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == ["host"]
    assert "brak przyjętej misji" in chat.snapshot().messages[-1].text
    engine.close()
