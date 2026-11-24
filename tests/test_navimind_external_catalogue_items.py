"""Acceptance of independent supplier items through existing WindowHub coordinator."""
from __future__ import annotations

from dataclasses import replace
import pytest

from app.agent.offers.navimind_external_catalogue_items import (
    ExternalComponent, ExternalItemKind, ExternalItemSpec, PriceState,
    ReferenceImage, build_external_draft,
)
from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRoute, TechnicalStatus, plan_commercial_quote,
)
from app.agent.runtime.navimind_virtual_windowhub import (
    VirtualWindowHub, run_virtual_mission,
)


def spec(kind=ExternalItemKind.DOOR_WITH_EXTERNAL_PANEL, **kw):
    values = dict(
        position_id="1", kind=kind, product_description="Drzwi wejściowe PCV",
        width_mm=1100, height_mm=2200, quantity=1, supplier="Veyna",
        supplier_model="EK-02-A",
        components=(
            ExternalComponent("Skrzydło i rama", "producent stolarki", "2700.00"),
            ExternalComponent("Panel EK-02-A", "zewnętrzny dostawca"),
        ),
    )
    values.update(kw)
    return ExternalItemSpec(**values)


def caps(**kw):
    values = dict(exact_catalogue_construction_verified=False,
                  description_field_verified=True, descriptive_position_supported=True,
                  placeholder_position_supported=True, image_insert_supported=True,
                  manual_price_field_verified=True,
                  available_placeholder_width_mm=1000,
                  available_placeholder_height_mm=1000)
    values.update(kw)
    return QuoteCapabilities(**values)


def test_external_panel_draft_keeps_supplier_code_and_real_requested_geometry():
    draft = build_external_draft(spec())
    assert draft.state == PriceState.COMPONENT_ONLY
    assert draft.task.allow_unpriced_draft
    assert draft.task.request.requested_width_mm == 1100
    assert draft.task.request.requested_height_mm == 2200
    assert "EK-02-A" in draft.task.request.description
    assert "Veyna" in draft.task.request.description
    assert "Skrzydło i rama" in draft.task.request.description
    assert draft.task.request.manual_unit_price is None
    assert not draft.exact_catalogue_product_verified


def test_known_door_frame_component_price_is_not_fake_total():
    draft = build_external_draft(spec())
    assert draft.components[0].verified_component_price == "2700.00"
    assert draft.task.request.manual_unit_price is None
    assert "component_prices_are_not_assembly_total" in draft.missing


def test_exterior_garage_door_can_be_prepared_without_catalogue_price():
    draft = build_external_draft(spec(
        ExternalItemKind.GARAGE_DOOR, product_description="Brama garażowa",
        supplier=None, supplier_model=None, components=(),
        width_mm=2900, height_mm=2400,
    ))
    assert draft.state == PriceState.UNKNOWN
    assert draft.task.request.requested_width_mm == 2900
    assert draft.task.request.manual_unit_price is None


def test_authorized_representative_image_is_clearly_not_product_proof():
    draft = build_external_draft(spec(
        illustration=ReferenceImage(
            "demo/example-panel.png", "Poglądowy wzór panelu",
            "materiał przykładowy od handlowca", True, True,
        ),
    ))
    assert draft.task.request.image_reference == "demo/example-panel.png"
    assert draft.task.request.image_use_authorized
    assert draft.display_image_is_representative
    assert "Ilustracja poglądowa" in draft.task.request.description


def test_unapproved_image_is_not_used_and_does_not_block_other_draft_work():
    draft = build_external_draft(spec(
        illustration=ReferenceImage("client.png", "Zdjęcie", "zewnętrzne", False),
    ))
    assert draft.task.request.image_reference is None
    assert "illustration_use_not_authorized_not_inserted" in draft.missing
    env = VirtualWindowHub("OFR/101", caps())
    trace = run_virtual_mission((draft.task,), env)
    assert trace.terminal_reason == "draft_partially_prepared_unpriced_positions"
    assert env.positions["1"].image_reference is None


def test_approved_complete_price_may_be_used_but_is_not_auto_saved():
    draft = build_external_draft(spec(
        approved_total_unit_price="5200.00",
        approved_price_source="handlowiec: zatwierdzona wycena zestawu",
        explicit_salesperson_price_approval=True,
    ))
    assert draft.state == PriceState.APPROVED_TOTAL
    assert draft.task.request.manual_unit_price == "5200.00"
    env = VirtualWindowHub("OFR/101", caps())
    trace = run_virtual_mission((draft.task,), env)
    assert trace.finished
    assert env.positions["1"].unit_price == "5200.00"
    assert not env.saved and not env.sent


def test_price_without_operator_approval_cannot_be_written():
    with pytest.raises(ValueError, match="approved_total_requires_salesperson"):
        spec(approved_total_unit_price="4400.00",
             approved_price_source="online listing")


def test_approval_without_price_is_invalid():
    with pytest.raises(ValueError, match="approval_without_total_price"):
        spec(explicit_salesperson_price_approval=True)


def test_multiple_external_products_continue_and_report_missing_prices():
    door = build_external_draft(spec(position_id="1"))
    garage = build_external_draft(spec(
        ExternalItemKind.GARAGE_DOOR, position_id="2", supplier=None,
        supplier_model=None, components=(), product_description="Brama segmentowa",
        width_mm=3000, height_mm=2400,
    ))
    env = VirtualWindowHub("OFR/101", caps())
    trace = run_virtual_mission((door.task, garage.task), env)
    assert set(env.positions) == {"1", "2"}
    assert trace.summary["unpriced_position_ids"] == ["1", "2"]
    assert trace.summary["draft_positions_prepared"] == 2
    assert not trace.finished
    assert not trace.summary["ready_for_final_customer_quote"]


def test_authorized_example_image_virtual_readback_and_missing_price_together():
    door = build_external_draft(spec(
        illustration=ReferenceImage(
            "demo/panel.png", "Zdjęcie wzorcowe", "dostarczone do demonstracji",
            True, True,
        ),
    ))
    env = VirtualWindowHub("OFR/101", caps())
    trace = run_virtual_mission((door.task,), env)
    assert env.positions["1"].image_reference == "demo/panel.png"
    assert trace.summary["positions"][0]["verified"]["image"]
    assert env.positions["1"].unit_price is None
    assert not trace.finished


def test_unavailable_image_editing_reveals_review_not_fake_success():
    door = build_external_draft(spec(
        illustration=ReferenceImage("demo/panel.png", "Przykład", "test", True),
    ))
    env = VirtualWindowHub("OFR/101", caps(image_insert_supported=False))
    trace = run_virtual_mission((door.task,), env)
    assert not trace.finished
    assert trace.terminal_reason == "image_requirements_unresolved"


def test_existing_catalogue_is_not_misrepresented_as_verified():
    door = build_external_draft(spec())
    assert door.task.technical.status == TechnicalStatus.NOT_CHECKED
    assert "do wyceny" in door.task.request.description.casefold()
    assert door.exact_catalogue_product_verified is False


@pytest.mark.parametrize("bad", ["", "-3", "NaN", "Infinity", "500 EUR"])
def test_invalid_component_price_not_accepted(bad):
    with pytest.raises(ValueError, match="invalid_price"):
        ExternalComponent("Rama", "supplier", bad)


def test_external_product_requires_positive_dimensions_and_quantity():
    with pytest.raises(ValueError, match="external_item_dimensions_required"):
        spec(width_mm=0)
    with pytest.raises(ValueError, match="external_item_dimensions_required"):
        spec(quantity=-1)


def test_model_needs_a_named_supplier():
    with pytest.raises(ValueError, match="model_needs_supplier"):
        spec(supplier=None)


def test_representative_image_without_provenance_is_rejected():
    with pytest.raises(ValueError, match="image_provenance_required"):
        ReferenceImage("path", "pic", "", True)


def test_duplicate_component_labels_are_rejected():
    with pytest.raises(ValueError, match="duplicate_component"):
        spec(components=(ExternalComponent("Panel", "first"),
                         ExternalComponent("panel", "second")))


def test_external_item_cannot_be_misclassified_as_catalogue_when_global_support_exists():
    draft = build_external_draft(spec())
    assert draft.task.request.force_non_catalogue
    plan = plan_commercial_quote(
        draft.task.request,
        caps(exact_catalogue_construction_verified=True),
        draft.task.technical,
    )
    assert plan.route == QuoteRoute.DESCRIPTIVE_PLACEHOLDER
    assert plan.representative_geometry
    assert plan.geometry_for_display == (1000, 1000)
    assert "1100 x 2200 mm" in plan.proposed_description


def test_existing_verified_normal_catalogue_quote_still_works():
    from app.agent.offers.windowhub_commercial_quote_routes import QuoteRequest
    regular = QuoteRequest("Okno katalogowe", 1,
                           requested_width_mm=1400, requested_height_mm=1300)
    external = build_external_draft(spec()).task.request
    assert regular.force_non_catalogue is False
    assert external.force_non_catalogue is True


def test_string_flags_cannot_implicitly_grant_photo_permission():
    with pytest.raises(ValueError, match="explicit_image_authorization_boolean_required"):
        ReferenceImage("path", "photo", "supplier", "False")


def test_string_flags_cannot_implicitly_grant_total_price_approval():
    with pytest.raises(ValueError, match="explicit_price_approval_boolean_required"):
        spec(
            approved_total_unit_price="4900.00",
            approved_price_source="unverified source",
            explicit_salesperson_price_approval="True",
        )


def test_catalogue_exclusion_must_not_be_missing_or_string():
    from app.agent.offers.windowhub_commercial_quote_routes import QuoteRequest
    with pytest.raises(ValueError, match="invalid_catalogue_exclusion_flag"):
        QuoteRequest("Pozycja", 1, force_non_catalogue="False")
