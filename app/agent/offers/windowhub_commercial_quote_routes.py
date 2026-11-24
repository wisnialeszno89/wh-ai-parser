"""Commercial quotation routes for WindowHub, independent of production approval.

A salesperson may quote a non-catalogue product using a descriptive line,
representative placeholder, image and separately evidenced manual price.
Manufacturer limitations are warnings, not a veto on preparing a quotation.
This module plans only; no file, price or UI is ever written by it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, InvalidOperation


class QuoteRoute(str, Enum):
    CATALOGUE = "catalogue"
    DESCRIPTIVE_PLACEHOLDER = "descriptive_placeholder"
    TEXT_ONLY = "text_only"
    MANUAL_REVIEW = "manual_review"


class TechnicalStatus(str, Enum):
    VERIFIED_COMPLIANT = "verified_compliant"
    KNOWN_OUTSIDE_WARRANTY = "known_outside_warranty"
    POTENTIALLY_NONCOMPLIANT = "potentially_noncompliant"
    NOT_CHECKED = "not_checked"


@dataclass(frozen=True)
class QuoteRequest:
    description: str
    quantity: int
    requested_width_mm: int | None = None
    requested_height_mm: int | None = None
    manual_unit_price: str | None = None
    currency: str = "PLN"
    image_reference: str | None = None
    image_use_authorized: bool = False
    allow_placeholder: bool = True
    customer_requires_exact_geometry: bool = False
    # A specific external item must never be assumed present merely because
    # WindowHub supports other catalogue products in this scene.
    force_non_catalogue: bool = False

    def __post_init__(self):
        if not self.description.strip():
            raise ValueError("description_required")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("invalid_quantity")
        for value in (self.requested_width_mm, self.requested_height_mm):
            if value is not None and (type(value) is not int or value <= 0):
                raise ValueError("invalid_dimension")
        if self.manual_unit_price is not None:
            try:
                value = Decimal(self.manual_unit_price)
            except (ValueError, InvalidOperation, TypeError) as exc:
                raise ValueError("invalid_manual_price") from exc
            if not value.is_finite() or value < 0:
                raise ValueError("invalid_manual_price")
        if not self.currency or len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("invalid_currency")


@dataclass(frozen=True)
class QuoteCapabilities:
    exact_catalogue_construction_verified: bool
    description_field_verified: bool
    descriptive_position_supported: bool
    placeholder_position_supported: bool
    image_insert_supported: bool
    manual_price_field_verified: bool
    available_placeholder_width_mm: int | None = None
    available_placeholder_height_mm: int | None = None


@dataclass(frozen=True)
class TechnicalFinding:
    status: TechnicalStatus
    summary: str
    reference: str | None = None

    def __post_init__(self):
        if not self.summary.strip():
            raise ValueError("technical_finding_summary_required")
        if self.status in (TechnicalStatus.KNOWN_OUTSIDE_WARRANTY, TechnicalStatus.VERIFIED_COMPLIANT):
            if not self.reference:
                raise ValueError("technical_finding_reference_required")


@dataclass(frozen=True)
class QuotePlan:
    route: QuoteRoute
    proposed_description: str
    geometry_for_display: tuple[int, int] | None
    representative_geometry: bool
    manual_unit_price: str | None
    manual_price_ready: bool
    image_reference: str | None
    image_ready: bool
    technical_status: TechnicalStatus
    warnings: tuple[str, ...]
    pending: tuple[str, ...]
    requires_salesperson_review: bool = True
    production_approved: bool = False
    save_authorized: bool = False
    send_authorized: bool = False


def plan_commercial_quote(
    request: QuoteRequest,
    capabilities: QuoteCapabilities,
    finding: TechnicalFinding,
) -> QuotePlan:
    """Prioritize answerability, preserve truthfulness about its technical status.

    A representative 1000x1000 placeholder must NEVER be silently interpreted
    as the customer's real dimensions, a buildable product, or a final price.
    A commercial quotation can be proposed outside warranty, but production
    approval stays entirely with a separate authorized human process.
    """
    warnings: list[str] = []
    pending: list[str] = []
    description = request.description.strip()

    if finding.status == TechnicalStatus.KNOWN_OUTSIDE_WARRANTY:
        warnings.append("outside_manufacturer_warranty:" + finding.summary)
        description += "\nUWAGA TECHNICZNA: Pozycja poza zakresem gwarancji producenta. " + finding.summary
    elif finding.status == TechnicalStatus.POTENTIALLY_NONCOMPLIANT:
        warnings.append("potential_technical_noncompliance:" + finding.summary)
        description += "\nDO WERYFIKACJI TECHNICZNEJ: " + finding.summary
    elif finding.status == TechnicalStatus.NOT_CHECKED:
        warnings.append("technical_compliance_not_checked")
        description += "\nStatus techniczny: niezweryfikowany."

    if capabilities.exact_catalogue_construction_verified and not request.force_non_catalogue:
        route = QuoteRoute.CATALOGUE
    elif (request.allow_placeholder and capabilities.placeholder_position_supported
          and capabilities.description_field_verified
          and capabilities.available_placeholder_width_mm is not None
          and capabilities.available_placeholder_height_mm is not None
          and not request.customer_requires_exact_geometry):
        route = QuoteRoute.DESCRIPTIVE_PLACEHOLDER
    elif capabilities.descriptive_position_supported and capabilities.description_field_verified:
        route = QuoteRoute.TEXT_ONLY
    else:
        route = QuoteRoute.MANUAL_REVIEW
        pending.append("no_verified_description_or_placeholder_route")

    display_geometry: tuple[int, int] | None = None
    representative = False
    if route == QuoteRoute.CATALOGUE:
        if request.requested_width_mm and request.requested_height_mm:
            display_geometry = (request.requested_width_mm, request.requested_height_mm)
        else:
            pending.append("requested_dimensions_missing_or_unverified")
    elif route == QuoteRoute.DESCRIPTIVE_PLACEHOLDER:
        display_geometry = (capabilities.available_placeholder_width_mm,
                            capabilities.available_placeholder_height_mm)
        representative = True
        original_dims = (
            f"{request.requested_width_mm} x {request.requested_height_mm} mm"
            if request.requested_width_mm and request.requested_height_mm
            else "wymiary docelowe nieustalone"
        )
        description = (
            "POZYCJA OPISOWA — GEOMETRIA W PROGRAMIE JEST WYŁĄCZNIE ZASTĘPCZA.\n"
            f"Wymiary wymagane przez klienta: {original_dims}.\n"
            + description
        )
        warnings.append("placeholder_dimensions_not_production_dimensions")
    elif route == QuoteRoute.TEXT_ONLY:
        description = "POZYCJA TEKSTOWA — NIE JEST KONSTRUKCJĄ KATALOGOWĄ.\n" + description

    price_ready = request.manual_unit_price is not None and capabilities.manual_price_field_verified
    if request.manual_unit_price is not None and not price_ready:
        pending.append("manual_price_entry_field_not_verified")
    if request.manual_unit_price is None:
        pending.append("price_not_supplied_do_not_invent")

    image_ready = bool(
        request.image_reference and request.image_use_authorized
        and capabilities.image_insert_supported
        and route != QuoteRoute.MANUAL_REVIEW
    )
    if request.image_reference and not image_ready:
        pending.append("image_insertion_not_authorized_or_unverified")

    if route == QuoteRoute.MANUAL_REVIEW:
        pending.append("salesperson_must_choose_quotation_representation")
    if finding.status != TechnicalStatus.VERIFIED_COMPLIANT:
        pending.append("technical_and_warranty_review_before_production")

    return QuotePlan(
        route=route,
        proposed_description=description,
        geometry_for_display=display_geometry,
        representative_geometry=representative,
        manual_unit_price=(request.manual_unit_price if price_ready else None),
        manual_price_ready=price_ready,
        image_reference=(request.image_reference if image_ready else None),
        image_ready=image_ready,
        technical_status=finding.status,
        warnings=tuple(warnings),
        pending=tuple(dict.fromkeys(pending)),
    )
