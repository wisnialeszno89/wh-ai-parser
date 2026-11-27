"""Portable controller tests: GUI buttons cannot bypass user control or V2 guards."""
import pytest

from app.agent.runtime.navimind_local_input_arbiter import InputOwner, InputDenied
from app.agent.runtime.navimind_panel_controller import (
    NaviMindPanelController, PanelMode,
)


def test_startup_is_human_first_and_disconnected():
    panel = NaviMindPanelController()
    s = panel.snapshot()
    assert s.mode == PanelMode.HUMAN
    assert s.human_controls
    assert not s.connected
    assert s.can_resume and not s.can_takeover
    assert panel.current_permit() is None


def test_resume_only_requests_fresh_reobservation():
    panel = NaviMindPanelController()
    result = panel.resume()
    assert result.mode == PanelMode.RESUME_PENDING
    assert not result.human_controls
    assert panel.arbiter.reobservation_required
    assert panel.current_permit() is None
    assert result.document_label == "Brak połączonego zadania"


def test_user_can_take_over_from_pending_resume():
    panel = NaviMindPanelController()
    panel.resume()
    old_epoch = panel.arbiter.epoch
    panel.takeover()
    assert panel.snapshot().mode == PanelMode.HUMAN
    assert panel.arbiter.owner == InputOwner.HUMAN
    assert panel.arbiter.epoch > old_epoch


def test_unconnected_panel_cannot_fake_verified_document():
    panel = NaviMindPanelController()
    panel.resume()
    with pytest.raises(ValueError, match="fresh_verified_connected_document_required"):
        panel.confirm_verified_resume(
            verified_document_key="OFR/1", verified_from_fresh_scene=True,
        )
    assert panel.current_permit() is None


def test_trusted_host_must_confirm_fresh_document_before_ready():
    panel = NaviMindPanelController()
    panel.connect_host()
    panel.resume()
    for key, fresh in (("", True), ("OFR/1", False), ("  ", True)):
        with pytest.raises(ValueError):
            panel.confirm_verified_resume(
                verified_document_key=key, verified_from_fresh_scene=fresh,
            )
    result = panel.confirm_verified_resume(
        verified_document_key="OFR/1", verified_from_fresh_scene=True,
    )
    assert result.mode == PanelMode.AGENT_READY
    assert panel.current_permit() is not None


def test_takeover_invalidates_previous_host_permission():
    panel = NaviMindPanelController()
    panel.connect_host()
    panel.resume()
    panel.confirm_verified_resume(
        verified_document_key="OFR/1", verified_from_fresh_scene=True,
    )
    permit = panel.current_permit()
    assert permit is not None
    panel.takeover()
    assert panel.current_permit() is None
    assert not panel.arbiter.permit_current(permit)
    with pytest.raises(InputDenied):
        panel.arbiter.dispatch(permit, lambda: pytest.fail("old click"))


def test_old_permit_does_not_survive_retake_resume_even_for_same_offer():
    panel = NaviMindPanelController()
    panel.connect_host()
    panel.resume()
    panel.confirm_verified_resume(
        verified_document_key="OFR/1", verified_from_fresh_scene=True,
    )
    stale = panel.current_permit()
    panel.takeover()
    panel.resume()
    assert panel.current_permit() is None
    assert not panel.arbiter.permit_current(stale)
    panel.confirm_verified_resume(
        verified_document_key="OFR/1", verified_from_fresh_scene=True,
    )
    assert panel.current_permit() != stale


def test_training_mode_is_human_owned_and_does_not_start_recording():
    panel = NaviMindPanelController()
    view = panel.training()
    assert view.mode == PanelMode.LEARNING
    assert view.human_controls
    assert panel.current_permit() is None
    assert "Zapamiętuję lokalne" in view.detail


def test_training_cannot_start_while_agent_ready():
    panel = NaviMindPanelController()
    panel.connect_host()
    panel.resume()
    panel.confirm_verified_resume(
        verified_document_key="OFR/1", verified_from_fresh_scene=True,
    )
    assert panel.training().mode == PanelMode.AGENT_READY


def test_stop_prevents_future_resume_and_cancels_permit():
    panel = NaviMindPanelController()
    panel.connect_host()
    panel.resume()
    panel.confirm_verified_resume(
        verified_document_key="OFR/1", verified_from_fresh_scene=True,
    )
    permit = panel.current_permit()
    status = panel.stop()
    assert status.mode == PanelMode.STOPPED
    assert status.human_controls
    assert not status.can_resume
    assert panel.current_permit() is None
    assert not panel.arbiter.permit_current(permit)
    assert panel.resume().mode == PanelMode.STOPPED
    with pytest.raises(ValueError, match="task_already_stopped"):
        panel.connect_host()


def test_stop_from_human_owned_state_keeps_human_priority():
    panel = NaviMindPanelController()
    status = panel.stop()
    assert status.mode == PanelMode.STOPPED
    assert status.human_controls
    assert panel.arbiter.owner == InputOwner.HUMAN


def test_subscriber_receives_initial_and_updated_snapshot():
    panel = NaviMindPanelController()
    observed = []
    panel.subscribe(observed.append)
    assert len(observed) == 1
    panel.training()
    assert len(observed) == 2
    assert observed[0].revision < observed[1].revision
    assert observed[1].mode == PanelMode.LEARNING


def test_resume_is_idempotent_until_new_human_interaction():
    panel = NaviMindPanelController()
    first = panel.resume()
    epoch = panel.arbiter.epoch
    second = panel.resume()
    assert second.mode == PanelMode.RESUME_PENDING
    assert first.revision == second.revision
    assert panel.arbiter.epoch == epoch


def test_no_business_persistence_authorized_by_panel():
    panel = NaviMindPanelController()
    assert not hasattr(panel, "send_offer")
    assert not hasattr(panel, "save_offer")
    assert panel.snapshot().connected is False


def test_external_takeover_mismatch_fails_closed_on_resume():
    panel = NaviMindPanelController()
    panel.resume()
    panel.takeover()
    assert panel.current_permit() is None
    with pytest.raises(ValueError):
        panel.confirm_verified_resume(
            verified_document_key="OFR/1", verified_from_fresh_scene=True,
        )


def test_panel_does_not_open_any_native_window_by_importing_state_controller():
    # Headless Codespaces: GUI is a separate launchable Tk process.
    panel = NaviMindPanelController()
    assert panel.snapshot().title == "Sterowanie ręczne"
