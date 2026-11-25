"""Offline Start1 -> picker -> exact OFR bootstrap contract; no Windows clicks."""
from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from app.agent.runtime.navimind_draft_bootstrap import (
    DRAFT_DOCUMENT_KEY, draft_offer_candidate,
    verify_draft_start, verify_draft_properties,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
from app.agent.runtime.navimind_work_mission import (
    WorkMissionCoordinator, WorkStage,
)


def scene(title="Okna - Start1", *, hwnd=10, app="Okna.exe", selected=None):
    elements = []
    if selected is not None:
        elements.append(SimpleNamespace(
            kind="tabitem", label=selected,
            metadata={"source": "windows_ui_automation", "uia_tab_scope": "document",
                      "uia_visible": True, "uia_selected": True,
                      "automation_id": "DOC_TAB", "uia_runtime_id": "selected-tab"},
        ))
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application=app, active_window_title=title),
            metadata={"window_handle": hwnd},
        ),
        elements=elements,
    )


def test_draft_start_is_only_exact_foreground_windowhub_start1():
    good = verify_draft_start(scene())
    assert good.valid and good.hwnd == 10
    for bad in (
        scene(title="Okna - OFR/100"),
        scene(title="Okna - Start1", app="notepad.exe"),
        scene(hwnd=0),
        scene(title="Okna - Start2"),
    ):
        assert not verify_draft_start(bad).valid


def test_native_properties_must_have_distinct_valid_window_handle():
    assert verify_draft_properties(
        scene("Właściwości dokumentu", hwnd=20), prior_hwnd=10,
    ).valid
    assert not verify_draft_properties(
        scene("Właściwości dokumentu", hwnd=10), prior_hwnd=10,
    ).valid
    assert not verify_draft_properties(
        scene("Zakładanie nowego klienta", hwnd=20), prior_hwnd=10,
    ).valid


def test_candidate_offer_is_not_invented_from_window_title_or_wrong_tab():
    real = scene("Okna - OFR/5061-", hwnd=10, selected="OFR/5061-")
    assert draft_offer_candidate(real) == "OFR/5061-"
    for other in (
        scene("Okna - OFR/5061-", hwnd=10),
        scene("Okna - OFR/5061-", hwnd=10, selected="OFR/5062-"),
        scene("Okna - ZLC/5061-", hwnd=10, selected="ZLC/5061-"),
        scene("Okna - OFR/5061-", hwnd=10, app="notepad.exe",
              selected="OFR/5061-"),
    ):
        assert draft_offer_candidate(other) is None


def test_draft_mission_requires_verified_selected_offer_to_bind_new_document():
    chat = MissionChat(document_key=DRAFT_DOCUMENT_KEY, arbiter=LocalInputArbiter())
    chat.user_message("Przygotuj nową ofertę.")
    coordinator = WorkMissionCoordinator(chat)
    mission = coordinator.queue_current()
    assert not coordinator.bind_verified_new_offer("OFR/5061-")
    coordinator.transition(
        mission.task_id, WorkStage.PAUSED,
        reason="draft_customer_selection_required",
    )
    assert not coordinator.bind_verified_new_offer("ZLC/5061-")
    assert coordinator.bind_verified_new_offer("OFR/5061-")
    changed = coordinator.current()
    assert changed.stage == WorkStage.READY
    assert changed.document_key == "OFR/5061-"
    assert changed.task_id == mission.task_id


def test_shared_host_reobserves_start_and_verified_properties_scope():
    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    chat_message = host.chat.user_message("Zrób nową ofertę.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(mission.task_id, WorkStage.READY)
    assert host.approve_current_work_for_resume(
        revision=chat_message.mission_revision,
        task_id=mission.task_id, coordinator=coordinator,
    )
    host.controller.resume()
    assert host.inspect_fresh_scene(scene()).verified
    assert host.controller.current_permit() is not None

    # Scope may only be established by the trusted executor AFTER readback.
    props = scene("Właściwości dokumentu", hwnd=22)
    assert host.note_verified_workflow_step(
        props, revision=mission.revision,
    )
    host._draft_phase = "properties"
    host.controller.takeover()
    host.release_for_reobservation()
    assert host.inspect_fresh_scene(props).verified
    assert not host.inspect_fresh_scene(
        scene("Właściwości dokumentu", hwnd=23),
    ).verified


def test_host_adopts_exact_selected_OFR_only_after_customer_handoff_and_callback(monkeypatch):
    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    host.chat.user_message("Nowa oferta z oknami.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(
        mission.task_id, WorkStage.PAUSED,
        reason="draft_customer_selection_required",
    )
    host._draft_phase = "awaiting_customer_selection"
    class NativeProof:
        offer = "OFR/7000-"
        def verify(self, _scene, _api):
            return "native_offer"
    host._draft_native_scope = NativeProof()
    import app.agent.runtime.windowhub_mdi_native_probe as mdi
    monkeypatch.setattr(mdi, "_Win32Mdi", lambda: object())
    host.draft_document_bound_callback = coordinator.bind_verified_new_offer
    assert host.approve_current_work_for_resume(
        revision=mission.revision, task_id=mission.task_id,
        coordinator=coordinator,
    )
    host.controller.resume()
    wrong = scene("Okna - OFR/7000-", selected="OFR/7001-")
    assert not host.inspect_fresh_scene(wrong).verified
    assert host.expected_offer == DRAFT_DOCUMENT_KEY
    good = scene("Okna - OFR/7000-", selected="OFR/7000-")
    assert host.inspect_fresh_scene(good).verified
    assert host.expected_offer == "OFR/7000-"
    assert host.chat.document_key == "OFR/7000-"
    assert coordinator.current().document_key == "OFR/7000-"
    assert coordinator.current().stage == WorkStage.READY


def test_draft_start_action_calls_only_shared_arbiter_and_native_invoke(monkeypatch):
    from app.agent.runtime import navimind_draft_bootstrap as bootstrap
    import tools.run_windowhub_new_offer_native_invoke_once as native
    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    message = host.chat.user_message("Utwórz nową roboczą ofertę.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(mission.task_id, WorkStage.READY)
    assert host.approve_current_work_for_resume(
        revision=message.mission_revision,
        task_id=mission.task_id, coordinator=coordinator,
    )
    host.controller.resume()
    initial = scene()
    assert host.inspect_fresh_scene(initial).verified
    calls = []
    class Invoke:
        def Invoke(self):
            calls.append("invoke")
    monkeypatch.setattr(
        native, "resolve_native_control",
        lambda _scene, **kwargs: Invoke(),
    )
    monkeypatch.setenv("WH_REAL_WINDOWHUB", "1")
    monkeypatch.setenv("COMPUTER_USE_LIVE", "1")
    import app.agent.runtime.windowhub_new_offer_handoff as native_scope
    import app.agent.runtime.windowhub_mdi_native_probe as mdi
    class Handoff:
        def before_confirm(self, _scene, _api):
            return True
    monkeypatch.setattr(native_scope.NewOfferHandoff, "begin",
                        lambda _scene, _api: Handoff())
    monkeypatch.setattr(mdi, "_Win32Mdi", lambda: object())
    class Loop:
        def __init__(self):
            self.steps = [initial, scene("Właściwości dokumentu", hwnd=25)]
        def observe_scene(self):
            return deepcopy(self.steps.pop(0))
    proof = bootstrap.safe_native_start_action(
        Loop(), host, mission_revision=mission.revision,
    )
    assert proof.valid and proof.stage == "document_properties"
    assert calls == ["invoke"]
    assert host._draft_phase == "properties"
    assert host.controller.current_permit() is None


def test_draft_pick_customer_requires_new_window_and_never_selects_row(monkeypatch):
    from app.agent.runtime import navimind_draft_bootstrap as bootstrap
    import tools.run_windowhub_new_offer_native_invoke_once as native
    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    msg = host.chat.user_message("Stwórz ofertę.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(mission.task_id, WorkStage.READY)
    host._draft_phase = "properties"
    host._draft_native_scope = SimpleNamespace(properties=25)
    monkeypatch.setenv("WH_REAL_WINDOWHUB", "1")
    monkeypatch.setenv("COMPUTER_USE_LIVE", "1")
    assert host.approve_current_work_for_resume(
        revision=msg.mission_revision, task_id=mission.task_id,
        coordinator=coordinator,
    )
    props = scene("Właściwości dokumentu", hwnd=25)
    assert host.note_verified_workflow_step(props, revision=mission.revision)
    host.controller.resume()
    assert host.inspect_fresh_scene(props).verified
    calls = []
    class Button:
        def click_input(self):
            calls.append("picker_only")
    monkeypatch.setattr(
        native, "resolve_native_wrapper",
        lambda _scene, **kwargs: Button(),
    )
    class Loop:
        def __init__(self):
            self.steps = [
                props,
                scene("Wybór klienta", hwnd=27),
            ]
        def observe_scene(self):
            return deepcopy(self.steps.pop(0))
    proof = bootstrap.safe_native_open_customer_picker(
        Loop(), host, mission_revision=mission.revision,
    )
    assert proof.valid
    assert calls == ["picker_only"]
    assert host._draft_phase == "awaiting_customer_selection"
    assert host.controller.current_permit() is None


def test_unsaved_native_position_handoff_continues_without_OFR_number(monkeypatch):
    import app.agent.runtime.windowhub_mdi_native_probe as mdi
    monkeypatch.setattr(mdi, "_Win32Mdi", lambda: object())
    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    msg = host.chat.user_message("Przygotuj niezapisaną ofertę.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(
        mission.task_id, WorkStage.PAUSED,
        reason="draft_customer_selection_required",
    )
    class Handoff:
        def verify(self, _scene, _api, **_kwargs):
            return "owned_position_transaction"
    host._draft_native_scope = Handoff()
    host._draft_phase = "awaiting_customer_selection"
    host.draft_unnumbered_ready_callback = (
        coordinator.begin_verified_unnumbered_draft
    )
    assert host.approve_current_work_for_resume(
        revision=msg.mission_revision, task_id=mission.task_id,
        coordinator=coordinator,
    )
    host.controller.resume()
    editor = scene("Dodawanie nowej pozycji", hwnd=35)
    assert host.inspect_fresh_scene(editor).verified
    assert host._draft_phase == "unsaved_position"
    assert host.expected_offer == DRAFT_DOCUMENT_KEY
    assert coordinator.current().stage == WorkStage.READY
    assert host.controller.current_permit() is not None


def test_unrelated_existing_offer_cannot_be_adopted_without_native_provenance():
    host = NaviMindSharedHost(DRAFT_DOCUMENT_KEY)
    msg = host.chat.user_message("Nowa oferta.")
    coordinator = WorkMissionCoordinator(host.chat)
    mission = coordinator.queue_current()
    coordinator.transition(
        mission.task_id, WorkStage.PAUSED,
        reason="draft_customer_selection_required",
    )
    host._draft_phase = "awaiting_customer_selection"
    host.draft_document_bound_callback = coordinator.bind_verified_new_offer
    assert host.approve_current_work_for_resume(
        revision=msg.mission_revision, task_id=mission.task_id,
        coordinator=coordinator,
    )
    host.controller.resume()
    assert not host.inspect_fresh_scene(
        scene("Okna - OFR/888-", selected="OFR/888-"),
    ).verified
    assert host.expected_offer == DRAFT_DOCUMENT_KEY
