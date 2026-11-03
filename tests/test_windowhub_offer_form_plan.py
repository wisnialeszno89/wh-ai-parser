import pytest

from app.agent.offers.agent_construction_compiler import AgentConstructionCompiler
from app.agent.offers.offer_context import OfferContext
from app.agent.offers.windowhub_offer_form_plan import (
    WindowHubOfferFormPlanBuilder,
    WindowHubPlanHandling,
)


def _context(**overrides):
    values = {
        "raw_request": "Okno 1200x1500 DKR",
        "width": 1200,
        "height": 1500,
        "quantity": 3,
        "product_type": "window",
        "profile": "VEKA_82",
        "opening": "RIGHT_TILT_TURN",
        "glazing": "triple",
    }
    values.update(overrides)
    return OfferContext(**values)


def _project(context):
    return AgentConstructionCompiler().compile(context)


def test_builds_non_executable_plan_from_context_and_compiled_project():
    context = _context()
    project = _project(context)

    plan = WindowHubOfferFormPlanBuilder().build(context, project)

    assert plan.is_valid is True
    assert plan.execution_enabled is False
    assert plan.requires_review is True

    by_name = {entry.field_name: entry for entry in plan.entries}
    assert by_name["item_type_window"].desired_value is True
    assert by_name["item_type_window"].handling == WindowHubPlanHandling.RADIO_SELECTION

    assert by_name["quantity_input"].desired_value == 3
    assert by_name["quantity_input"].handling == WindowHubPlanHandling.DIRECT_VALUE

    assert by_name["width_1"].desired_value == 1200
    assert by_name["height_1"].desired_value == 1500
    assert by_name["width_1"].handling == WindowHubPlanHandling.MAPPING_UNVERIFIED
    assert by_name["height_1"].handling == WindowHubPlanHandling.MAPPING_UNVERIFIED

    assert by_name["profile_system_picker"].desired_value == {
        "manufacturer": "VEKA",
        "system": "Softline 82 MD",
    }
    assert by_name["profile_system_picker"].handling == WindowHubPlanHandling.CATALOG_SELECTION

    assert by_name["glazing_package"].desired_value == "3glass"
    assert by_name["glazing_package"].handling == WindowHubPlanHandling.CATALOG_SELECTION


def test_plan_does_not_invent_glazing_when_context_and_project_are_invalid():
    context = _context(quantity=0)
    project = _project(context)

    plan = WindowHubOfferFormPlanBuilder().build(context, project)

    assert plan.is_valid is False
    assert plan.entries == ()
    assert "context_conflict:invalid_quantity" in plan.blockers
    assert plan.execution_enabled is False


def test_plan_blocks_when_compiled_dimensions_do_not_match_context():
    context = _context()
    project = _project(context)
    project.schema.width = 1300

    plan = WindowHubOfferFormPlanBuilder().build(context, project)

    assert plan.is_valid is False
    assert "compiled_dimensions_do_not_match_offer_context" in plan.blockers
    assert plan.entries == ()


def test_plan_blocks_missing_construction_project():
    context = _context()

    plan = WindowHubOfferFormPlanBuilder().build(context, None)

    assert plan.is_valid is False
    assert "construction_project_missing" in plan.blockers
    assert plan.entries == ()


def test_plan_blocks_non_window_product_type():
    context = _context(product_type="door")
    project = _project(context)

    plan = WindowHubOfferFormPlanBuilder().build(context, project)

    assert plan.is_valid is False
    assert "unsupported_product_type_for_window_wizard" in plan.blockers
    assert plan.entries == ()


def test_plan_keeps_inside_and_outside_colors_separate_and_unverified():
    context = _context(
        color_inside="white",
        color_outside="anthracite",
    )
    project = _project(context)

    plan = WindowHubOfferFormPlanBuilder().build(context, project)

    assert plan.is_valid is True
    color_entry = next(
        entry for entry in plan.entries
        if entry.field_name is None
    )
    assert color_entry.desired_value == {
        "inside": "",
        "outside": "7016",
    }
    assert color_entry.handling == WindowHubPlanHandling.MAPPING_UNVERIFIED
    assert (
        "inside_outside_profile_color_mapping_unverified"
        in plan.review_items
    )


def test_plan_flags_multi_segment_geometry_for_review():
    context = _context(
        raw_request="Okno 2000x1500 DKR + FIX",
        width=2000,
        openings=("RIGHT_TILT_TURN", "FIX"),
        opening=None,
    )
    project = _project(context)

    plan = WindowHubOfferFormPlanBuilder().build(context, project)

    assert plan.is_valid is True
    assert (
        "multi_segment_construction_requires_geometry_mapping"
        in plan.review_items
    )
    assert plan.execution_enabled is False


def test_builder_rejects_wrong_input_type():
    with pytest.raises(TypeError, match="windowhub_offer_plan_context_invalid"):
        WindowHubOfferFormPlanBuilder().build("not-context", None)
