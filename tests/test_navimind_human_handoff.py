"""Codespaces tests for explicit human takeover and interruption-safe resume."""
from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask
from app.agent.runtime.navimind_virtual_windowhub import VirtualWindowHub
from app.agent.runtime.navimind_virtual_desktop_workspace import (
    PinnedMissionSession, VirtualDesktopWorkspace,
)
from app.agent.runtime.navimind_human_handoff import (
    ControlOwner, HandoffStatus, HumanHandoffController,
)


def setup():
    c = QuoteCapabilities(
        exact_catalogue_construction_verified=False,
        description_field_verified=True,
        descriptive_position_supported=True,
        placeholder_position_supported=True,
        image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )
    env = VirtualWindowHub("OFR/PRIMARY", c)
    other = VirtualWindowHub("OFR/OTHER", c)
    task = PositionTask(
        "1", QuoteRequest("Nietypowe okno", quantity=1, requested_width_mm=2000,
                          requested_height_mm=2400, manual_unit_price="2800.00"),
        TechnicalFinding(TechnicalStatus.NOT_CHECKED, "Sprawdzić parametry"),
    )
    workspace = VirtualDesktopWorkspace(
        {"OFR/PRIMARY": env, "OFR/OTHER": other},
        foreground_document="OFR/PRIMARY",
    )
    session = PinnedMissionSession("OFR/PRIMARY", (task,))
    return HumanHandoffController(session), workspace, env, other


def complete(ctrl, space, limit=20):
    for _ in range(limit):
        event = ctrl.tick(space)
        if event.status == HandoffStatus.AGENT_COMPLETE:
            return event
        assert event.status == HandoffStatus.AGENT_ACTION, event.reason
    raise AssertionError("did not finish")


def test_user_can_pause_before_any_action():
    ctrl, space, env, _ = setup()
    event = ctrl.take_over()
    assert event.status == HandoffStatus.PAUSED_BY_HUMAN
    assert ctrl.tick(space).status == HandoffStatus.PAUSED_BY_HUMAN
    assert env.positions == {}
    assert ctrl.owner == ControlOwner.HUMAN


def test_release_resumes_at_actual_position_without_recreating_it():
    ctrl, space, env, _ = setup()
    assert ctrl.tick(space).action == "create_position"
    ctrl.take_over()
    assert ctrl.tick(space).status == HandoffStatus.PAUSED_BY_HUMAN
    ctrl.release()
    assert complete(ctrl, space).status == HandoffStatus.AGENT_COMPLETE
    assert env.attempted_actions.count(("1", "create_position")) == 1
    assert not env.saved and not env.sent


def test_stale_model_plan_epoch_is_invalid_even_after_release():
    ctrl, space, env, _ = setup()
    epoch = ctrl.epoch
    ctrl.take_over()
    ctrl.release()
    assert not ctrl.is_action_epoch_current(epoch)
    result = ctrl.tick(space, prepared_epoch=epoch)
    assert result.status == HandoffStatus.RESUME_BLOCKED
    assert result.reason == "stale_plan_epoch_reobserve"
    assert env.positions == {}
    assert ctrl.tick(space, prepared_epoch=ctrl.epoch).status == HandoffStatus.AGENT_ACTION


def test_foreground_offer_change_blocks_then_resumes_when_restored():
    ctrl, space, env, other = setup()
    ctrl.take_over()
    space.select_document("OFR/OTHER")
    ctrl.release()
    assert ctrl.tick(space).status == HandoffStatus.RESUME_BLOCKED
    assert other.positions == {}
    space.select_document("OFR/PRIMARY")
    assert complete(ctrl, space).status == HandoffStatus.AGENT_COMPLETE


def test_user_can_interrupt_after_description_and_then_resume():
    ctrl, space, env, _ = setup()
    assert ctrl.tick(space).action == "create_position"
    assert ctrl.tick(space).action == "write_description"
    ctrl.take_over()
    for _ in range(4):
        assert ctrl.tick(space).status == HandoffStatus.PAUSED_BY_HUMAN
    ctrl.release()
    assert complete(ctrl, space).status == HandoffStatus.AGENT_COMPLETE
    assert env.attempted_actions.count(("1", "write_description")) == 1


def test_manual_price_change_requires_review_no_overwrite():
    ctrl, space, env, _ = setup()
    complete(ctrl, space)
    ctrl.take_over()
    env.positions["1"].unit_price = "3200.00"
    ctrl.release()
    outcome = ctrl.tick(space)
    assert outcome.status == HandoffStatus.NEEDS_REVIEW
    assert outcome.reason == "external_operator_edit_requires_review"
    assert env.positions["1"].unit_price == "3200.00"
    assert ctrl.tick(space).status == HandoffStatus.NEEDS_REVIEW


def test_clear_review_without_approved_replan_does_not_silently_accept_change():
    ctrl, space, env, _ = setup()
    complete(ctrl, space)
    env.positions["1"].description = "Ręcznie poprawione"
    assert ctrl.tick(space).status == HandoffStatus.NEEDS_REVIEW
    ctrl.clear_review_after_operator_replan()
    assert ctrl.tick(space).status == HandoffStatus.NEEDS_REVIEW
    assert env.positions["1"].description == "Ręcznie poprawione"


def test_pause_does_not_reset_no_progress_history():
    ctrl, space, env, _ = setup()
    env.injected_noops.add(("1", "create_position"))
    assert ctrl.tick(space).status == HandoffStatus.NEEDS_REVIEW
    assert env.attempted_actions == [("1", "create_position")]
    ctrl.take_over()
    ctrl.release()
    ctrl.clear_review_after_operator_replan()
    assert ctrl.tick(space).status == HandoffStatus.NEEDS_REVIEW
    assert env.attempted_actions == [("1", "create_position")]


def test_pause_resume_rejects_invalid_epoch_types():
    ctrl, space, env, _ = setup()
    assert not ctrl.is_action_epoch_current(True)
    assert not ctrl.is_action_epoch_current("0")
    assert ctrl.is_action_epoch_current(0)
    assert ctrl.tick(space, prepared_epoch=-1).status == HandoffStatus.RESUME_BLOCKED


def test_multiple_pause_release_operations_never_authorize_stale_plan():
    ctrl, space, env, _ = setup()
    prepared = ctrl.epoch
    for _ in range(3):
        ctrl.take_over()
        ctrl.release()
    assert ctrl.tick(space, prepared_epoch=prepared).status == HandoffStatus.RESUME_BLOCKED
    assert env.positions == {}
    assert ctrl.tick(space, prepared_epoch=ctrl.epoch).status == HandoffStatus.AGENT_ACTION
