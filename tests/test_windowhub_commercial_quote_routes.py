import pytest

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, QuoteRequest, QuoteRoute, TechnicalFinding,
    TechnicalStatus, plan_commercial_quote,
)


def capabilities(**changes):
    params = dict(
        exact_catalogue_construction_verified=False,
        description_field_verified=True,
        descriptive_position_supported=True,
        placeholder_position_supported=True,
        image_insert_supported=True,
        manual_price_field_verified=True,
        available_placeholder_width_mm=1000,
        available_placeholder_height_mm=1000,
    )
    params.update(changes)
    return QuoteCapabilities(**params)


def finding(status=TechnicalStatus.NOT_CHECKED, summary="Brak weryfikacji"):
    return TechnicalFinding(status, summary, "Winkhaus:verified-doc" if status in {
        TechnicalStatus.KNOWN_OUTSIDE_WARRANTY,
        TechnicalStatus.VERIFIED_COMPLIANT,
    } else None)


def request(**changes):
    params = dict(description="Nietypowy produkt — oferta opisowa", quantity=1,
                  requested_width_mm=2300, requested_height_mm=2700)
    params.update(changes)
    return QuoteRequest(**params)


def test_commercial_draft_allowed_outside_warranty_with_visible_warning():
    plan = plan_commercial_quote(
        request(manual_unit_price="3250.00"),
        capabilities(),
        finding(TechnicalStatus.KNOWN_OUTSIDE_WARRANTY, "Przekroczone gabaryty"),
    )
    assert plan.route == QuoteRoute.DESCRIPTIVE_PLACEHOLDER
    assert plan.representative_geometry
    assert plan.geometry_for_display == (1000, 1000)
    assert "2300 x 2700 mm" in plan.proposed_description
    assert "POZYCJA OPISOWA" in plan.proposed_description
    assert "poza zakresem gwarancji" in plan.proposed_description
    assert plan.manual_unit_price == "3250.00"
    assert not plan.production_approved
    assert not plan.save_authorized
    assert not plan.send_authorized


def test_exact_verified_catalogue_remains_preferred():
    plan = plan_commercial_quote(
        request(),
        capabilities(exact_catalogue_construction_verified=True),
        finding(TechnicalStatus.VERIFIED_COMPLIANT, "Pozycja zgodna"),
    )
    assert plan.route == QuoteRoute.CATALOGUE
    assert plan.geometry_for_display == (2300, 2700)
    assert not plan.representative_geometry


def test_text_only_when_placeholder_unavailable():
    plan = plan_commercial_quote(
        request(),
        capabilities(placeholder_position_supported=False),
        finding(),
    )
    assert plan.route == QuoteRoute.TEXT_ONLY
    assert "POZYCJA TEKSTOWA" in plan.proposed_description


def test_no_description_capability_requires_operator():
    plan = plan_commercial_quote(
        request(),
        capabilities(description_field_verified=False),
        finding(),
    )
    assert plan.route == QuoteRoute.MANUAL_REVIEW
    assert "no_verified_description_or_placeholder_route" in plan.pending


def test_customer_requires_exact_geometry_disables_substitute_dimensions():
    plan = plan_commercial_quote(
        request(customer_requires_exact_geometry=True),
        capabilities(),
        finding(),
    )
    assert plan.route == QuoteRoute.TEXT_ONLY
    assert not plan.representative_geometry


def test_unverified_manual_price_not_fabricated_or_entered():
    plan = plan_commercial_quote(
        request(manual_unit_price="4500.00"),
        capabilities(manual_price_field_verified=False),
        finding(),
    )
    assert not plan.manual_price_ready
    assert plan.manual_unit_price is None
    assert "manual_price_entry_field_not_verified" in plan.pending


def test_image_needs_explicit_authorization_and_ui_support():
    not_approved = plan_commercial_quote(
        request(image_reference="images/example.png", image_use_authorized=False),
        capabilities(), finding(),
    )
    assert not not_approved.image_ready
    assert not_approved.image_reference is None
    assert "image_insertion_not_authorized_or_unverified" in not_approved.pending
    approved = plan_commercial_quote(
        request(image_reference="images/example.png", image_use_authorized=True),
        capabilities(), finding(),
    )
    assert approved.image_ready
    assert approved.image_reference == "images/example.png"


def test_no_invented_price_or_technical_compliance():
    plan = plan_commercial_quote(request(), capabilities(), finding())
    assert plan.manual_unit_price is None
    assert "price_not_supplied_do_not_invent" in plan.pending
    assert "technical_compliance_not_checked" in plan.warnings
    assert "technical_and_warranty_review_before_production" in plan.pending


@pytest.mark.parametrize("price", ["-1", "NaN", "Infinity", "500 EUR", ""])
def test_invalid_manual_price_rejected(price):
    with pytest.raises(ValueError, match="invalid_manual_price"):
        request(manual_unit_price=price)


def test_unverified_warranty_assertion_is_not_allowed():
    with pytest.raises(ValueError, match="technical_finding_reference_required"):
        TechnicalFinding(TechnicalStatus.KNOWN_OUTSIDE_WARRANTY, "Wykracza poza gwarancję")
