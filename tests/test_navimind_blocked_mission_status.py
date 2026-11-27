"""A blocked quote remains in coordinator history, never claims GUI work."""
from pathlib import Path

from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_work_mission import WorkMissionCoordinator, WorkStage

ROOT = Path(__file__).resolve().parents[1]


def test_blocked_offer_is_locally_registered_without_native_action():
    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    original = chat.user_message("Przygotuj niezapisaną ofertę dla dwóch okien")
    coordinator = WorkMissionCoordinator(chat)
    mission = coordinator.queue_current()
    assert mission is not None
    assert mission.message_id == original.message_id
    paused = coordinator.transition(
        mission.task_id, WorkStage.PAUSED, reason="v2_endpoint_missing"
    )
    assert paused is not None
    assert paused.stage == WorkStage.PAUSED
    assert paused.reason == "v2_endpoint_missing"
    assert paused.total_verified_actions == 0
    assert coordinator.is_current(paused)

    chat.user_message("Podaj aktualny stan lokalnych narzędzi")
    # The previous quote remains reportable but its authorization is stale.
    assert coordinator.current().task_id == mission.task_id
    assert not coordinator.is_current(coordinator.current())


def test_host_registers_blocked_mission_and_reports_staleness():
    code = (ROOT / "tools/run_navimind_shared_control_center.py").read_text(
        encoding="utf-8"
    )
    assert "mission = work_coordinator.queue_current()" in code
    assert "WorkStage.PAUSED, reason=v2_blocker" in code
    assert "Potwierdzone kroki GUI: 0" in code
    assert "stale = not work_coordinator.is_current(mission)" in code
    assert "nieaktualna po nowej wiadomości" in code
