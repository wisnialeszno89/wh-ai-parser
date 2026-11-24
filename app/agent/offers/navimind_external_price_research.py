"""Price lookup is explicitly opt-in and produces advisory evidence only.

A caller may supply observed public listings or supplier catalog entries.
This module NEVER browses on its own and never writes a quoted price.
Marketplace comparisons are not proof of identical item specifications,
warranty, VAT, delivery, installation, stock or validity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from urllib.parse import urlsplit


class PriceSourceKind(str, Enum):
    SUPPLIER_CATALOGUE = "supplier_catalogue"
    MANUFACTURER_CATALOGUE = "manufacturer_catalogue"
    MARKETPLACE = "marketplace"
    RETAILER = "retailer"


@dataclass(frozen=True)
class PriceReference:
    source_kind: PriceSourceKind
    source_url: str
    seller: str
    title: str
    observed_price: str
    currency: str
    checked_on: str
    comparable_category: str
    product_code: str | None = None
    width_mm: int | None = None
    height_mm: int | None = None
    includes_vat: bool | None = None
    shipping_included: bool | None = None
    installation_included: bool | None = None

    def __post_init__(self):
        if not isinstance(self.source_kind, PriceSourceKind):
            raise ValueError("invalid_price_source_type")
        parts = urlsplit(self.source_url)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            raise ValueError("price_requires_public_https_source")
        if not all(isinstance(x, str) and x.strip() for x in (
            self.seller, self.title, self.currency, self.checked_on,
            self.comparable_category,
        )):
            raise ValueError("incomplete_price_reference")
        if not self.currency.isalpha() or len(self.currency) != 3:
            raise ValueError("invalid_currency")
        try:
            if (len(self.checked_on) != 10 or date.fromisoformat(self.checked_on).isoformat()
                    != self.checked_on):
                raise ValueError("invalid_checked_date")
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid_checked_date") from exc
        try:
            price = Decimal(self.observed_price)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("invalid_market_price") from exc
        if not price.is_finite() or price < 0:
            raise ValueError("invalid_market_price")
        for dimension in (self.width_mm, self.height_mm):
            if dimension is not None and (type(dimension) is not int or dimension <= 0):
                raise ValueError("invalid_market_dimensions")


@dataclass(frozen=True)
class PriceResearchRequest:
    item_category: str
    requested_by_salesperson: bool
    product_code: str | None = None
    width_mm: int | None = None
    height_mm: int | None = None
    currency: str = "PLN"


@dataclass(frozen=True)
class PriceSuggestion:
    reference: PriceReference
    comparison: str
    warnings: tuple[str, ...]
    verified_total_for_quotation: bool = False
    approved_to_write: bool = False


def review_price_references(
    request: PriceResearchRequest,
    references: tuple[PriceReference, ...],
) -> tuple[PriceSuggestion, ...]:
    """Review externally observed references only after human request.

    Even exact code and geometry are NOT enough for automatically declaring
    a valid final customer price. Sources may include accessories without
    the door, different tax rates, finish options or transport conditions.
    """
    if request.requested_by_salesperson is not True:
        return ()
    if not isinstance(request.item_category, str) or not request.item_category.strip():
        raise ValueError("price_research_category_required")
    suggestions: list[PriceSuggestion] = []
    for reference in references:
        if reference.comparable_category.casefold() != request.item_category.casefold():
            continue
        code_match = bool(request.product_code and reference.product_code
                          and reference.product_code.casefold() == request.product_code.casefold())
        dimensions_match = (
            request.width_mm is not None and request.height_mm is not None
            and reference.width_mm == request.width_mm
            and reference.height_mm == request.height_mm
        )
        if code_match and dimensions_match:
            comparison = "matching_code_and_dimensions_unverified_other_terms"
        elif code_match:
            comparison = "matching_code_different_or_unknown_dimensions"
        else:
            comparison = "similar_category_only"
        warnings = ["market_reference_not_approved_quote_price"]
        if reference.currency != request.currency:
            warnings.append("currency_differs_conversion_not_performed")
        if not dimensions_match:
            warnings.append("dimensions_not_proven_equivalent")
        if not code_match:
            warnings.append("product_model_not_proven_equivalent")
        if reference.includes_vat is None:
            warnings.append("vat_inclusion_unknown")
        if reference.shipping_included is not True:
            warnings.append("transport_not_verified_in_price")
        if reference.installation_included is not True:
            warnings.append("installation_not_verified_in_price")
        suggestions.append(PriceSuggestion(
            reference, comparison, tuple(warnings),
        ))
    return tuple(suggestions)
