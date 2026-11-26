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
