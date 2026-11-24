"""Portable coordinator tests; no Windows, API or actual file writes."""
from dataclasses import replace

import pytest

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import (
    MissionAction, MissionScene, PositionReadback, PositionTask,
    mission_progress_summary, next_mission_intent,
)
from app.agent.runtime.portable_editor_skills import EditorTarget


def capabilities(**kwargs):
    defaults = dict(
        exact_catalogue_construction_verified=False,
        description_field_verified=True, descriptive_position_supported=True,
        placeholder_position_supported=True, image_insert_supported=True,
        manual_price_field_verified=True, available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )
    defaults.update(kwargs)
    return QuoteCapabilities(**defaults)


def task(position_id="1", **kwargs):
    defaults = dict(
        description="Konstrukcja nietypowa — wycena handlowa",
        quantity=1, requested_width_mm=2400, requested_height_mm=2750,
        manual_unit_price="3400.00",
    )
    defaults.update(kwargs)
    return PositionTask(
        position_id, QuoteRequest(**defaults),
        TechnicalFinding(TechnicalStatus.KNOWN_OUTSIDE_WARRANTY,
                         "Zbyt duże gabaryty", "manufacturer-note-17"),
    )


def scene(position="1", **kwargs):
    defaults = dict(
        application="WindowHub", document_id="OFR/TEST", document_identity_verified=True,
        fresh=True, active_position_id=position,
        quote_capabilities=capabilities(),
        editor_target=EditorTarget("WindowHub", "OFR/TEST", position,
                                   "description", True, True, True, True),
    )
    defaults.update(kwargs)
    return MissionScene(**defaults)


def rb(position="1", **kwargs):
    defaults = dict(
        position_id=position, document_id="OFR/TEST",
        fresh=True, exact_position=True,
    )
    defaults.update(kwargs)
    return PositionReadback(**defaults)


def test_new_position_never_claimed_created():
    intent = next_mission_intent((task(),), scene())
    assert intent.action == MissionAction.CREATE_POSITION
    assert intent.proposed_route.value == "descriptive_placeholder"
    assert intent.requires_v2_executor is True
    assert intent.verified_completed is False
    assert "outside_manufacturer_warranty" in " ".join(intent.warnings)


def test_write_description_after_creation_is_verified():
    status = rb(created_verified=True)
    intent = next_mission_intent((task(),), scene(), (status,))
    assert intent.action == MissionAction.WRITE_DESCRIPTION
    assert "2400 x 2750 mm" in intent.description
    assert "Zbyt duże gabaryty" in intent.description


def test_image_then_manual_price_then_complete():
    first = task(image_reference="photo.png", image_use_authorized=True)
    status = rb(created_verified=True, description_verified=True)
    assert next_mission_intent((first,), scene(), (status,)).action == MissionAction.INSERT_IMAGE
    status = replace(status, image_verified=True)
    intent = next_mission_intent((first,), scene(), (status,))
    assert intent.action == MissionAction.SET_MANUAL_PRICE
    assert intent.price == "3400.00"
    status = replace(status, price_verified=True)
    assert next_mission_intent((first,), scene(), (status,)).action == MissionAction.COMPLETE
    summary = mission_progress_summary((first,), scene(), (status,))
    assert summary["all_position_requirements_verified"]
    assert not summary["agent_authorized_to_save"]
    assert not summary["production_approval"]


def test_multiple_positions_advance_only_after_first_is_verified():
    tasks = (task("1"), task("2", requested_width_mm=900))
    first = rb("1", created_verified=True, description_verified=True, price_verified=True)
    intent = next_mission_intent(tasks, scene(position="2"), (first,))
    assert intent.position_id == "2"
    assert intent.action == MissionAction.CREATE_POSITION


def test_stale_or_wrong_document_readback_cannot_complete():
    status = rb(created_verified=True, description_verified=True,
                price_verified=True, document_id="OFR/OTHER")
    assert next_mission_intent((task(),), scene(), (status,)).action == MissionAction.CREATE_POSITION
    assert next_mission_intent((task(),), scene(fresh=False), (status,)).action == MissionAction.OBSERVE


def test_text_editor_with_wrong_position_never_receives_description():
    status = rb(created_verified=True)
    intent = next_mission_intent((task(),), scene(position="2"), (status,))
    assert intent.action == MissionAction.OBSERVE
    assert intent.reason.startswith("description_editor:")


def test_no_price_is_not_quotation_completion():
    item = task(manual_unit_price=None)
    status = rb(created_verified=True, description_verified=True)
    intent = next_mission_intent((item,), scene(), (status,))
    assert intent.action == MissionAction.REVIEW
    assert intent.reason == "catalogue_or_external_price_requires_independent_readback"
    assert not mission_progress_summary((item,), scene(), (status,))["all_position_requirements_verified"]


def test_missing_manual_price_editor_blocks_wrong_price():
    status = rb(created_verified=True, description_verified=True)
    intent = next_mission_intent((task(),), scene(quote_capabilities=capabilities(
        manual_price_field_verified=False)), (status,))
    assert intent.action == MissionAction.REVIEW
    assert intent.price is None


def test_photo_permission_is_not_inferred():
    item = task(image_reference="photo.png", image_use_authorized=False)
    status = rb(created_verified=True, description_verified=True)
    assert next_mission_intent((item,), scene(), (status,)).action == MissionAction.REVIEW


def test_repeat_without_progress_escalates_instead_of_recreating():
    intent = next_mission_intent(
        (task(),), scene(),
        attempted_without_progress=("1:create_position",),
    )
    assert intent.action == MissionAction.REVIEW
    assert not intent.requires_v2_executor


def test_disallow_duplicate_tasks():
    with pytest.raises(ValueError, match="nonempty_unique_positions_required"):
        next_mission_intent((task("1"), task("1")), scene())


def test_unavailable_quote_representation_requires_review():
    intent = next_mission_intent(
        (task(),),
        scene(quote_capabilities=capabilities(
            description_field_verified=False,
            placeholder_position_supported=False,
            descriptive_position_supported=False,
        )),
    )
    assert intent.action == MissionAction.REVIEW
