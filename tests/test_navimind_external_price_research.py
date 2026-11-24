"""No market price is used without explicit request and human review."""
import pytest

from app.agent.offers.navimind_external_price_research import (
    PriceReference, PriceResearchRequest, PriceSourceKind,
    review_price_references,
)


def reference(**kwargs):
    values = dict(
        source_kind=PriceSourceKind.MARKETPLACE,
        source_url="https://example.org/listing/123",
        seller="Example seller",
        title="Panel dekoracyjny — przykład",
        observed_price="750.00", currency="PLN",
        checked_on="2026-11-24",
        comparable_category="door_panel",
        product_code="EK-02-A",
        width_mm=1100, height_mm=2200,
    )
    values.update(kwargs)
    return PriceReference(**values)


def request(**kwargs):
    values = dict(item_category="door_panel", requested_by_salesperson=True,
                  product_code="EK-02-A", width_mm=1100, height_mm=2200)
    values.update(kwargs)
    return PriceResearchRequest(**values)


def test_market_research_not_requested_returns_no_price_suggestions():
    result = review_price_references(
        request(requested_by_salesperson=False), (reference(),)
    )
    assert result == ()


def test_exact_matching_product_still_needs_operator_approval():
    results = review_price_references(request(), (reference(),))
    assert len(results) == 1
    assert results[0].comparison == "matching_code_and_dimensions_unverified_other_terms"
    assert not results[0].approved_to_write
    assert not results[0].verified_total_for_quotation
    assert "market_reference_not_approved_quote_price" in results[0].warnings


def test_similar_listing_is_not_claimed_same_product():
    results = review_price_references(
        request(), (reference(product_code="OTHER", width_mm=1000),)
    )
    assert results[0].comparison == "similar_category_only"
    assert "dimensions_not_proven_equivalent" in results[0].warnings
    assert "product_model_not_proven_equivalent" in results[0].warnings


def test_matching_code_but_wrong_geometry_is_flagged():
    results = review_price_references(
        request(), (reference(height_mm=2100),)
    )
    assert results[0].comparison == "matching_code_different_or_unknown_dimensions"


def test_foreign_currency_not_converted_or_hidden():
    results = review_price_references(
        request(), (reference(currency="EUR"),)
    )
    assert "currency_differs_conversion_not_performed" in results[0].warnings
    assert results[0].reference.observed_price == "750.00"


def test_unknown_delivery_tax_installation_are_flagged():
    results = review_price_references(request(), (reference(),))
    warnings = results[0].warnings
    assert "vat_inclusion_unknown" in warnings
    assert "transport_not_verified_in_price" in warnings
    assert "installation_not_verified_in_price" in warnings


def test_unrelated_category_does_not_get_wrong_price():
    result = review_price_references(
        request(), (reference(comparable_category="garage_door"),)
    )
    assert result == ()


def test_public_https_provenance_required():
    for url in ("http://example.org", "file:///tmp/p.html",
                "https://name:pass@example.org/a", "not-a-url"):
        with pytest.raises(ValueError, match="price_requires_public_https_source"):
            reference(source_url=url)


def test_invalid_market_price_is_refused():
    for price in ("NaN", "-1", "Infinity", "free", ""):
        with pytest.raises(ValueError, match="invalid_market_price"):
            reference(observed_price=price)


def test_missing_source_or_observation_date_is_refused():
    with pytest.raises(ValueError, match="incomplete_price_reference"):
        reference(checked_on="")
    with pytest.raises(ValueError, match="invalid_checked_date"):
        reference(checked_on="20261124")


def test_empty_request_requires_clear_category():
    with pytest.raises(ValueError, match="price_research_category_required"):
        review_price_references(request(item_category=" "), (reference(),))


def test_no_network_or_gui_side_effects_are_exposed():
    offer = review_price_references(request(), (reference(),))[0]
    assert not hasattr(offer, "write_price")
    assert not hasattr(offer, "buy")
    assert not hasattr(offer, "download")
