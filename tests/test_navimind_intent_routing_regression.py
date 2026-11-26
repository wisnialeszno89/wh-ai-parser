"""Regression for tool intent ambiguity and duplicate paused offer request."""
from app.agent.runtime.navimind_live_conversation import (
    explicit_document_sharing_help_request,
    explicit_local_mission_status_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_work_mission import WorkMissionCoordinator, WorkStage


def test_gui_consent_and_any_construction_does_not_trigger_document_help():
    question = (
        "Wyjaśnij różnicę między konfiguracją V2, połączeniem z serwerem, "
        "moją zgodą na sterowanie oraz potwierdzeniem wykonania kroku. "
        "Czy w WindowHub utworzono już jakąkolwiek konstrukcję? "
        "Odpowiadaj tylko na podstawie potwierdzonych danych."
    )
    assert not explicit_document_sharing_help_request(question)
    assert explicit_local_mission_status_request(question)


def test_explicit_document_sharing_questions_still_work():
    assert explicit_document_sharing_help_request(
        "Jak zatwierdzić udostępnienie dokumentu klienta?"
    )
    assert explicit_document_sharing_help_request(
        "Jak mam to zrobić",
        "Wybierz Przeanalizuj dokument w NaviMind.",
    )
    assert not explicit_document_sharing_help_request(
        "Jakie zatwierdzenie jest potrzebne przed klikaniem w WindowHub?"
    )
    assert not explicit_document_sharing_help_request(
        "Jak mam to zrobić",
        "Aby sterować WindowHub, kliknij lokalnie Wznów pracę."
    )
    assert not explicit_document_sharing_help_request(
        "Wyjaśnij moją zgodę na sterowanie i wykonanie konstrukcji."
    )


def test_duplicate_queued_offer_preserves_exclusions_without_resuming():
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    coordinator = WorkMissionCoordinator(chat)
    chat.user_message("Bez dodatkowych opcji, montażu, demontażu i wykończenia.")
    goal = "Przygotuj nową niezapisaną ofertę dla dwóch okien."
    chat.user_message(goal)
    first = coordinator.queue_current()
    assert first is not None
    assert first.service_exclusions == (
        "dodatkowe opcje", "montaż", "demontaż", "wykończenie"
    )
    first_paused = coordinator.transition(
        first.task_id, WorkStage.PAUSED, reason="v2_endpoint_missing",
    )
    assert first_paused is not None
    chat.user_message(goal)
    repeated = coordinator.queue_current()
    assert repeated is not None
    assert repeated.task_id != first.task_id
    assert repeated.service_exclusions == first.service_exclusions
    assert repeated.stage == WorkStage.QUEUED
    assert repeated.total_verified_actions == 0


def test_explicit_stage_and_control_count_uses_local_uia_not_process_presence():
    import time
    from app.agent.runtime.navimind_live_conversation import (
        LiveMissionConversation, explicit_windowhub_stage_read_request,
    )
    from app.agent.runtime.navimind_tool_router import ReadOnlyTool

    prompt = (
        "NaviMind, znajdź WindowHub w tle i odczytaj jego bieżący etap "
        "oraz liczbę kontrolek UIA. Nie zmieniaj aktywnego okna."
    )
    assert explicit_windowhub_stage_read_request(prompt)

    class NoModel:
        def reply(self, **kwargs):
            raise AssertionError("observation must be based on local host")

    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    calls = []
    engine = LiveMissionConversation(
        chat, NoModel(), read_only_tools={
            "inspect_windowhub": ReadOnlyTool(
                "inspect_windowhub", "Read UIA only",
                lambda: calls.append(True) or
                "Odczyt UIA: etap multiple_windows, 2 okna, 38 kontrolek.",
            )
        },
    )
    message = chat.user_message(prompt)
    assert engine.submit_current_message(message.message_id)
    deadline = time.monotonic() + 5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not engine.status().active
    assert calls == [True]
    assert "38 kontrolek" in chat.snapshot().messages[-1].text
    engine.close()
