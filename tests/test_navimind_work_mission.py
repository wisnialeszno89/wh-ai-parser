"""Offline tests for chat-pinned WindowHub work missions.

These tests do not operate Windows, call the V2 server, or perform GUI input.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_work_mission import (
    BackgroundWorkMission, WorkMissionCoordinator, WorkStage,
    WorkStepResult,
)


def new_chat():
    return MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())


def test_current_human_message_is_exact_mission_goal_not_model_generated():
    chat = new_chat()
    first = chat.user_message("Zrób roboczą ofertę na 4 okna dla Top Trans.")
    queue = WorkMissionCoordinator(chat)
    mission = queue.queue_current()
    assert mission.goal == first.text
    assert mission.document_key == "OFR/101"
    assert mission.message_id == first.message_id
    assert mission.revision == first.mission_revision
    assert mission.stage == WorkStage.QUEUED
    assert queue.queue_current() == mission


def test_new_human_message_invalidates_old_model_plan_and_step():
    chat = new_chat()
    chat.user_message("Zmień wymiar.")
    queue = WorkMissionCoordinator(chat)
    old = queue.queue_current()
    chat.user_message("Nie zmieniaj wymiaru. Przygotuj sam opis.")
    assert queue.transition(old.task_id, WorkStage.READY) is None
    assert queue.cancel_stale()
    assert queue.current() is None
    new = queue.queue_current()
    assert new.goal == "Nie zmieniaj wymiaru. Przygotuj sam opis."
    assert new.task_id != old.task_id


def test_successful_steps_are_budgeted_and_do_not_grant_native_authority():
    chat = new_chat()
    chat.user_message("Przygotuj ofertę.")
    queue = WorkMissionCoordinator(chat, max_cycles=1)
    mission = queue.queue_current()
    finished = queue.transition(
        mission.task_id, WorkStage.PAUSED,
        count_step=True, signature="fingerprint", observed_stage="offer_document",
    )
    assert finished.cycles == 1
    assert finished.last_verified_signature == "fingerprint"
    assert finished.last_verified_stage == "offer_document"
    blocked = queue.transition(
        mission.task_id, WorkStage.PAUSED, count_step=True,
    )
    assert blocked.stage == WorkStage.REVIEW
    assert blocked.reason == "mission_action_budget_exhausted"
    assert blocked.cycles == 1


def test_background_planning_delivers_verified_advisory_without_executor(monkeypatch):
    from app.agent.runtime import navimind_work_mission as module
    chat = new_chat()
    chat.user_message("Dopisz cztery konstrukcje.")
    queue = WorkMissionCoordinator(chat)
    results = []
    executions = []

    def fake_step(*, mission, loop, reasoner, host, execute):
        executions.append(execute)
        return WorkStepResult("ready", "safe_plan", "write_text")

    monkeypatch.setattr(module, "plan_or_execute_windowhub_step", fake_step)
    host = SimpleNamespace(
        controller=SimpleNamespace(current_permit=lambda: None)
    )
    worker = BackgroundWorkMission(
        queue, host=host, callback=lambda m, r: results.append((m, r)),
        loop_factory=lambda: object(), reasoner_factory=lambda: object(),
    )
    assert "Zadanie przyjęte" in worker.queue_and_plan()
    deadline = time.monotonic() + 5
    while not results and time.monotonic() < deadline:
        time.sleep(.01)
    assert len(results) == 1
    assert results[0][0].stage == WorkStage.READY
    assert results[0][1].action == "write_text"
    assert executions == [False]
    assert not worker.execute_one_authorized_step()
    worker.close()


def test_no_model_result_can_resurrect_stale_work_from_previous_turn():
    chat = new_chat()
    chat.user_message("Oferta A")
    queue = WorkMissionCoordinator(chat)
    old = queue.queue_current()
    queue.transition(old.task_id, WorkStage.THINKING)
    chat.user_message("Oferta B")
    assert queue.transition(
        old.task_id, WorkStage.READY, suggested_action="click_screen_element"
    ) is None
    assert queue.queue_current().goal == "Oferta B"


def test_tk_event_pump_keeps_windowhub_observations_independent_of_work_events():
    """No mission event should be needed for fresh UIA observation to resume."""
    import ast
    from pathlib import Path
    source = (
        Path(__file__).resolve().parents[1] /
        "tools" / "run_navimind_shared_control_center.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    pumps = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "pump"
    ]
    assert len(pumps) == 1
    loops = [node for node in pumps[0].body if isinstance(node, ast.While)]
    assert len(loops) == 2
    first_text = ast.get_source_segment(source, loops[0])
    second_text = ast.get_source_segment(source, loops[1])
    assert "work_events.get_nowait()" in first_text
    assert "queue.get_nowait()" in second_text
    assert "queue.get_nowait()" not in first_text


def test_work_mission_receives_only_approved_document_evidence():
    chat = new_chat()
    chat.user_message("Przygotuj cztery okna.")
    consent = [0, ""]
    queue = WorkMissionCoordinator(
        chat, document_snapshot_provider=lambda: tuple(consent),
    )
    first = queue.queue_current()
    assert not first.approved_document_evidence
    assert first.document_access_version == 0
    consent[:] = [1, "PDF 1: 1500x1400 mm, 2 szyby; klient TOP TRANS"]
    assert not queue.is_current(first)
    second = queue.queue_current()
    assert second.task_id != first.task_id
    assert second.document_access_version == 1
    assert "1500x1400" in second.approved_document_evidence
    assert queue.is_current(second)


def test_document_consent_revocation_invalidates_live_mission_even_without_chat_change():
    chat = new_chat()
    chat.user_message("Przygotuj ofertę z PDF.")
    consent = [3, "Zatwierdzone zapytanie klienta."]
    queue = WorkMissionCoordinator(
        chat, document_snapshot_provider=lambda: tuple(consent),
    )
    mission = queue.queue_current()
    assert queue.transition(mission.task_id, WorkStage.READY)
    consent[:] = [4, ""]
    assert not queue.is_current(mission)
    assert queue.transition(mission.task_id, WorkStage.EXECUTING) is None
    assert queue.cancel_stale()


def test_doc_consent_epoch_in_chat_increments_on_approval_and_revocation():
    from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
    engine = LiveMissionConversation(new_chat(), None)
    v0, initial = engine.document_access_snapshot()
    assert initial is None
    engine.approve_document_context("Wymiary 1000 x 1500")
    v1, approved = engine.document_access_snapshot()
    assert v1 > v0 and "1000 x 1500" in approved
    engine.revoke_document_context()
    v2, after = engine.document_access_snapshot()
    assert v2 > v1 and after is None
    engine.close()


def test_work_step_before_dispatch_requires_current_consent_and_revision():
    import inspect
    from app.agent.runtime.navimind_work_mission import plan_or_execute_windowhub_step
    source = inspect.getsource(plan_or_execute_windowhub_step)
    assert "is_mission_current()" in source
    assert "stale_or_revoked_mission_before_dispatch" in source


def test_work_budget_is_enforced_before_native_dispatch_even_with_ready_mission(monkeypatch):
    from app.agent.runtime import navimind_work_mission as module
    chat = new_chat()
    chat.user_message("Uzupełnij ofertę.")
    queue = WorkMissionCoordinator(chat, max_cycles=1)
    mission = queue.queue_current()
    queue.transition(mission.task_id, WorkStage.READY)
    queue.transition(mission.task_id, WorkStage.PAUSED, count_step=True)
    queue.transition(mission.task_id, WorkStage.READY)
    host = SimpleNamespace(controller=SimpleNamespace(current_permit=lambda: object()))
    worker = BackgroundWorkMission(queue, host=host)
    monkeypatch.setenv("WH_REAL_WINDOWHUB", "1")
    monkeypatch.setenv("COMPUTER_USE_LIVE", "1")
    assert not worker.execute_one_authorized_step()
    assert queue.current().stage == WorkStage.REVIEW
    worker.close()


def test_unapproved_pdf_is_never_included_in_v2_mission_goal():
    from pathlib import Path
    launcher = (Path(__file__).resolve().parents[1] /
                "tools" / "run_navimind_shared_control_center.py").read_text(
                    encoding="utf-8")
    assert "document_snapshot_provider=approved_document_for_work" in launcher
    assert "if not snapshot:" in launcher
    assert "if (intake.status()[\"has_enquiry\"]" in launcher
    assert "and not live_chat.document_context_active()" in launcher
