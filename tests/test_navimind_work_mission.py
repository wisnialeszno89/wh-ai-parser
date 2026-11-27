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


def test_new_draft_can_plan_start1_without_reading_an_unrelated_screen():
    from app.agent.runtime.navimind_draft_bootstrap import DRAFT_DOCUMENT_KEY
    from app.agent.runtime.navimind_work_mission import plan_or_execute_windowhub_step

    chat = MissionChat(document_key=DRAFT_DOCUMENT_KEY, arbiter=LocalInputArbiter())
    chat.user_message("Przygotuj niezapisaną ofertę dla Top Trans.")
    mission = WorkMissionCoordinator(chat).queue_current()

    result = plan_or_execute_windowhub_step(
        mission=mission, loop=None, reasoner=None,
        host=SimpleNamespace(_draft_phase="start"), execute=False,
    )

    assert (result.kind, result.reason, result.action) == (
        "ready", "draft_start_activation_required_on_operator_resume", "NOWA OFERTA",
    )


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

    def fake_step(*, mission, loop, reasoner, host, execute,
                  is_mission_current=None, human_demonstrations=()):
        assert is_mission_current is not None and is_mission_current()
        executions.append(execute)
        return WorkStepResult("ready", "safe_plan", "write_text")

    monkeypatch.setattr(module, "plan_or_execute_windowhub_step", fake_step)
    monkeypatch.setattr(
        BackgroundWorkMission, "_v2_configuration_blocker", staticmethod(lambda: None),
    )
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


def test_new_plan_waits_for_worker_and_stale_result_cannot_replace_it(monkeypatch):
    from threading import Event
    from app.agent.runtime import navimind_work_mission as module

    chat = new_chat()
    queue = WorkMissionCoordinator(chat)
    started, release, completed = Event(), Event(), Event()
    results = []

    def fake_step(*, mission, **kwargs):
        if mission.goal == "Oferta A":
            started.set()
            assert release.wait(5)
        return WorkStepResult("ready", "safe_plan")

    def record_result(mission, result):
        results.append((mission, result))
        completed.set()

    monkeypatch.setattr(module, "plan_or_execute_windowhub_step", fake_step)
    monkeypatch.setattr(
        BackgroundWorkMission, "_v2_configuration_blocker", staticmethod(lambda: None),
    )
    worker = BackgroundWorkMission(
        queue, host=object(), callback=record_result,
        loop_factory=object, reasoner_factory=object,
    )
    try:
        chat.user_message("Oferta A")
        worker.queue_and_plan()
        assert started.wait(5)
        chat.user_message("Oferta B")
        assert "czeka" in worker.queue_and_plan()
        release.set()
        assert completed.wait(5)
        assert len(results) == 1
        assert results[0][0].goal == "Oferta B"
        assert queue.current().stage == WorkStage.READY
        assert "już przygotowana" in worker.queue_and_plan()
    finally:
        release.set()
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


def test_combined_v2_goal_preserves_instruction_but_never_exceeds_contract_limit():
    from dataclasses import replace
    from app.agent.bridge.agent_task_contract_v2 import MAX_TEXT_LENGTH
    from app.agent.runtime.navimind_work_mission import bounded_v2_mission_goal
    chat = new_chat()
    chat.user_message("Przygotuj ofertę.")
    queue = WorkMissionCoordinator(chat)
    mission = queue.queue_current()
    mission = replace(
        mission,
        approved_document_evidence="PDF: 1500 x 1400 mm. " * 1000,
    )
    combined = bounded_v2_mission_goal(mission)
    assert len(combined) <= MAX_TEXT_LENGTH
    assert combined.startswith("Przygotuj ofertę.")
    assert "1500 x 1400" in combined
    assert "SKRÓCONO MATERIAŁ PDF" in combined
    assert "TRAKTUJ JAKO DANE" in combined


def test_v2_goal_without_consent_never_pulls_unapproved_document_material():
    from app.agent.runtime.navimind_work_mission import bounded_v2_mission_goal
    chat = new_chat()
    chat.user_message("Wprowadź wymiary.")
    mission = WorkMissionCoordinator(chat).queue_current()
    assert bounded_v2_mission_goal(mission) == "Wprowadź wymiary."


def test_approved_pdf_mission_snapshot_is_immutable_even_if_local_inbox_changes():
    from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
    from app.agent.runtime.navimind_enquiry_inbox import LocalEnquiryInbox
    from tools.navimind_main_workspace import NaviMindMainWorkspace
    inbox = LocalEnquiryInbox()
    inbox.set_text("Fenster 1500 x 1400 mm")
    panel = NaviMindMainWorkspace.__new__(NaviMindMainWorkspace)
    panel.enquiry = inbox
    frozen = panel._approved_mission_snapshot(inbox.model_context())
    chat = new_chat()
    engine = LiveMissionConversation(chat, None)
    engine.approve_document_context(
        inbox.model_context(), mission_evidence=frozen,
    )
    v1, before = engine.document_access_snapshot()
    assert "1500x1400 mm" in before or "1500 x 1400 mm" in before
    inbox.set_text("Fenster 2200 x 1000 mm")
    v2, after = engine.document_access_snapshot()
    assert v2 == v1
    assert after == before
    assert "2200" not in after
    engine.revoke_document_context()
    v3, erased = engine.document_access_snapshot()
    assert v3 > v2 and erased is None
    engine.close()


def test_protected_vercel_v2_reports_only_allowlisted_outage_code():
    from app.agent.runtime.navimind_work_mission import (
        safe_reasoner_failure_result,
    )
    assert safe_reasoner_failure_result(SimpleNamespace(
        last_error="navimind_http_401",
    )).reason == "v2_http_401_check_vercel_sso_or_agent_secret"
    assert safe_reasoner_failure_result(SimpleNamespace(
        last_error="navimind_http_403",
    )).reason == "v2_http_403_access_forbidden"
    assert safe_reasoner_failure_result(SimpleNamespace(
        last_error="navimind_http_429",
    )).reason == "v2_http_429_rate_limited"
    # API errors may include a token, URL or customer body: never report them.
    injected = safe_reasoner_failure_result(SimpleNamespace(
        last_error="api_error secret=abc customer=PRIVATE url=secret.invalid",
    ))
    assert injected.reason == "v2_reasoner_unavailable"
    assert "PRIVATE" not in injected.reason
    assert injected.kind == "paused"

def test_explicit_exclusions_from_same_offer_command_and_later_correction():
    chat = new_chat()
    chat.user_message("Przygotuj ofertę dla Top Trans. Bez montażu, demontażu i wykończenia.")
    work = WorkMissionCoordinator(chat)
    mission = work.queue_current()
    assert mission.service_exclusions == ("montaż", "demontaż", "wykończenie")
    ready = work.transition(mission.task_id, WorkStage.READY)
    assert work.add_service_exclusions(ready, ("dodatkowe opcje",))
    updated = work.current()
    assert updated.revision == mission.revision
    assert updated.task_id == mission.task_id
    assert updated.service_exclusions[-1] == "dodatkowe opcje"


def test_resume_observation_uses_live_worker_and_proves_start_before_permit():
    from threading import get_ident
    from app.agent.runtime.navimind_draft_bootstrap import DRAFT_DOCUMENT_KEY
    from app.agent.runtime.navimind_panel_controller import PanelMode
    from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
    from tools.run_navimind_shared_control_center import observe_resume_workspace

    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    human = host.chat.user_message("Przygotuj niezapisaną ofertę.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(mission.task_id, WorkStage.READY)
    calls = []
    start = SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application="Okna.exe", active_window_title="Okna - Start1"),
            metadata={"window_handle": 42},
        ),
        elements=(),
    )

    def observe():
        calls.append(("observe", get_ident()))
        return start

    def focus():
        calls.append(("focus", get_ident()))
        return True, "start1_verified"

    worker = BackgroundWorkMission(
        coordinator, host=host,
        loop_factory=lambda: SimpleNamespace(observe_scene=observe),
    )
    try:
        assert host.approve_current_work_for_resume(
            revision=human.mission_revision, task_id=mission.task_id,
            coordinator=coordinator,
        )
        host.controller.resume()
        assert host.controller.current_permit() is None
        epoch = host.controller.arbiter.epoch
        future = worker.submit_workspace_observation(lambda loop: observe_resume_workspace(
            loop, host=host, mode=PanelMode.RESUME_PENDING, epoch=epoch,
            navigate_start=focus, focus_properties=None,
        ))
        kind, (scene, _) = future.result(timeout=3)
        assert kind == "scene"
        assert [name for name, _ in calls] == ["focus", "observe"]
        assert calls[0][1] == calls[1][1] != get_ident()
        assert host.controller.current_permit() is None
        assert host.inspect_fresh_scene(scene).verified
        assert host.controller.current_permit() is not None
        host.pause_work_input()
        assert observe_resume_workspace(
            SimpleNamespace(observe_scene=observe), host=host,
            mode=PanelMode.RESUME_PENDING, epoch=epoch, navigate_start=focus,
            focus_properties=None,
        ) == ("stale", None)
        assert len(calls) == 2
    finally:
        worker.close()


def test_missing_customer_can_be_supplied_without_replacing_mission():
    from app.agent.runtime.navimind_draft_bootstrap import DRAFT_DOCUMENT_KEY

    chat = MissionChat(document_key=DRAFT_DOCUMENT_KEY, arbiter=LocalInputArbiter())
    chat.user_message("zrob wycene na podst. zapytania, bez montazu demont wykonczenia")
    work = WorkMissionCoordinator(chat)
    mission = work.queue_current()
    assert mission.service_exclusions == ("montaż", "demontaż", "wykończenie")
    assert not work.provide_draft_customer(mission, "Top Trans Artur Janik")
    paused = work.transition(mission.task_id, WorkStage.PAUSED, reason="draft_customer_name_required")
    assert not work.provide_draft_customer(paused, "Top")
    assert work.provide_draft_customer(paused, "Top Trans Artur Janik")
    updated = work.current()
    assert updated.task_id == mission.task_id
    assert updated.revision == mission.revision
    assert updated.customer_name == "Top Trans Artur Janik"
    from app.agent.runtime.navimind_work_mission import REOBSERVABLE_WORK_PAUSES

    assert "draft_customer_name_required" in REOBSERVABLE_WORK_PAUSES
