"""Unpriced positions: work ahead safely, report gaps, never invent prices."""
from __future__ import annotations

from dataclasses import replace

import pytest

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import (
    MissionAction, MissionScene, PositionReadback, PositionTask,
    mission_progress_summary, next_mission_intent,
)
from app.agent.runtime.navimind_virtual_windowhub import (
    VirtualWindowHub, run_virtual_mission,
)


def capabilities(**override):
    values = dict(
        exact_catalogue_construction_verified=False,
        description_field_verified=True,
        descriptive_position_supported=True,
        placeholder_position_supported=True,
        image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )
    values.update(override)
    return QuoteCapabilities(**values)


def task(position, *, description="Parapet zewnętrzny", price=None,
         allow=True, width=1800):
    return PositionTask(
        position,
        QuoteRequest(description, 1, requested_width_mm=width,
                     requested_height_mm=250, manual_unit_price=price),
        TechnicalFinding(TechnicalStatus.NOT_CHECKED,
                         "Brak danych producenta dla parapetu"),
        allow_unpriced_draft=allow,
    )


def scene(active=None, **kwargs):
    return MissionScene("WindowHub", "OFR/101", True, True, active,
                        kwargs.get("capabilities", capabilities()))


def rb(position, *, created=True, description=True, price=False, fresh=True,
       document="OFR/101", exact=True):
    return PositionReadback(
        position, created_verified=created,
        description_verified=description, price_verified=price,
        document_id=document, fresh=fresh, exact_position=exact,
    )


def test_missing_price_can_continue_to_next_position_after_verified_description():
    tasks = (task("1"), task("2", description="Okno", price="2300.00"))
    next_step = next_mission_intent(
        tasks, scene(active="2"), (rb("1"),),
    )
    assert next_step.action == MissionAction.CREATE_POSITION
    assert next_step.position_id == "2"
    assert next_step.price is None


def test_unpriced_position_is_not_reported_as_fully_complete():
    tasks = (task("1"),)
    result = next_mission_intent(tasks, scene(active="1"), (rb("1"),))
    assert result.action == MissionAction.COMPLETE
    assert not result.verified_completed
    assert result.missing == ("price_unverified:1",)
    report = mission_progress_summary(tasks, scene(active="1"), (rb("1"),))
    assert report["unpriced_position_ids"] == ["1"]
    assert report["draft_positions_prepared"] == 1
    assert not report["all_position_requirements_verified"]
    assert not report["ready_for_final_customer_quote"]
    assert not report["agent_authorized_to_save"]
    assert not report["agent_authorized_to_send"]


def test_no_permission_remains_blocking_as_in_older_missions():
    tasks = (task("1", allow=False),)
    result = next_mission_intent(tasks, scene(active="1"), (rb("1"),))
    assert result.action == MissionAction.REVIEW
    assert result.reason == "catalogue_or_external_price_requires_independent_readback"


def test_unavailable_manual_price_field_is_deferred_only_with_permission():
    caps = capabilities(manual_price_field_verified=False)
    item = task("1", price="125.00")
    first = next_mission_intent((item,), scene(capabilities=caps))
    assert first.action == MissionAction.CREATE_POSITION
    later = next_mission_intent(
        (item,), scene(active="1", capabilities=caps), (rb("1"),),
    )
    assert later.action == MissionAction.COMPLETE
    assert "price_unverified:1" in later.missing


def test_unavailable_manual_price_field_without_permission_requires_review():
    item = task("1", price="125.00", allow=False)
    result = next_mission_intent(
        (item,), scene(capabilities=capabilities(manual_price_field_verified=False)),
    )
    assert result.action == MissionAction.REVIEW
    assert result.reason == "requested_manual_price_field_unavailable"


def test_no_value_is_written_as_zero_or_dummy_price():
    env = VirtualWindowHub("OFR/101", capabilities())
    item = task("1")
    result = run_virtual_mission((item,), env)
    assert result.terminal_reason == "draft_partially_prepared_unpriced_positions"
    assert not result.finished
    assert env.positions["1"].unit_price is None
    assert ("1", "set_manual_price") not in env.attempted_actions
    assert "price_not_supplied_do_not_invent" in result.summary["positions"][0]["pending"]
    assert env.positions["1"].description is not None
    assert env.saved is False and env.sent is False


def test_multiple_positions_finish_with_single_missing_price_report():
    env = VirtualWindowHub("OFR/101", capabilities())
    tasks = (
        task("1", width=1700),
        task("2", description="Okno PCV", price="2800.00", width=1300),
        task("3", description="Parapet boczny", width=800),
    )
    result = run_virtual_mission(tasks, env)
    assert result.terminal_reason == "draft_partially_prepared_unpriced_positions"
    assert set(env.positions) == {"1", "2", "3"}
    assert env.positions["2"].unit_price == "2800.00"
    assert env.positions["1"].unit_price is None
    assert env.positions["3"].unit_price is None
    assert result.summary["unpriced_position_ids"] == ["1", "3"]
    assert result.summary["draft_positions_prepared"] == 3
    assert not result.finished
    assert env.saved is False and env.sent is False


def test_when_price_readback_verified_position_does_not_report_missing():
    item = task("1")
    status = rb("1", price=True)
    result = next_mission_intent((item,), scene(active="1"), (status,))
    assert result.action == MissionAction.COMPLETE
    assert result.verified_completed
    report = mission_progress_summary((item,), scene(active="1"), (status,))
    assert report["unpriced_position_ids"] == []


def test_stale_readback_never_proves_geometry_or_description():
    item = task("1")
    result = next_mission_intent(
        (item,), scene(active="1"), (rb("1", fresh=False),),
    )
    assert result.action == MissionAction.CREATE_POSITION


def test_image_requirements_not_silently_skipped_by_price_deferral():
    item = PositionTask(
        "1",
        QuoteRequest("Parapet", 1, image_reference="unknown.png",
                     image_use_authorized=False),
        TechnicalFinding(TechnicalStatus.NOT_CHECKED, "Sprawdzić"),
        allow_unpriced_draft=True,
    )
    result = next_mission_intent(
        (item,), scene(active="1"), (rb("1"),),
    )
    assert result.action == MissionAction.REVIEW
    assert result.reason == "image_requirements_unresolved"


def test_unknown_creation_route_not_ignored_when_price_missing():
    item = task("1")
    result = next_mission_intent(
        (item,), scene(capabilities=capabilities(
            description_field_verified=False,
            placeholder_position_supported=False,
            descriptive_position_supported=False,
        )),
    )
    assert result.action == MissionAction.REVIEW
    assert result.reason == "quotation_route_requires_salesperson"


def test_repeated_failed_create_is_not_masked_by_price_deferral():
    result = next_mission_intent(
        (task("1"),), scene(),
        attempted_without_progress=("1:create_position",),
    )
    assert result.action == MissionAction.REVIEW


def test_explicit_permission_requires_boolean():
    with pytest.raises(ValueError, match="invalid_unpriced_draft_permission"):
        replace(task("1"), allow_unpriced_draft="yes")
