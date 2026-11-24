"""Draft out-of-catalogue WindowHub items without pretending to know prices.

Products may come from independent manufacturers (door infill panels, garage
doors, sills, accessories). The adapter uses the *existing* quotation
coordinator and its independent readback requirements.

An illustration is never product evidence; a known price for one component
never becomes the total price for an assembly. No network or GUI I/O here.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteRequest, TechnicalFinding, TechnicalStatus,
)
from app.agent.runtime.navimind_mission_coordinator import PositionTask


class ExternalItemKind(str, Enum):
    DOOR_WITH_EXTERNAL_PANEL = "door_with_external_panel"
    GARAGE_DOOR = "garage_door"
    EXTERIOR_SILL = "exterior_sill"
    EXTERNAL_ACCESSORY = "external_accessory"
    OTHER = "other"


class PriceState(str, Enum):
    UNKNOWN = "unknown"
    COMPONENT_ONLY = "component_only"
    MARKET_REFERENCE_ONLY = "market_reference_only"
    APPROVED_TOTAL = "approved_total"


@dataclass(frozen=True)
class ExternalComponent:
    name: str
    source: str
    # Informational, NOT equivalent to a complete product price.
    verified_component_price: str | None = None

    def __post_init__(self):
        if not self.name.strip() or not self.source.strip():
            raise ValueError("component_identity_required")
        if self.verified_component_price is not None:
            _check_price(self.verified_component_price)


@dataclass(frozen=True)
class ReferenceImage:
    path_or_reference: str
    description: str
    source: str
    use_authorized: bool
    representative_only: bool = True

    def __post_init__(self):
        if not self.path_or_reference.strip() or not self.description.strip() or not self.source.strip():
            raise ValueError("image_provenance_required")


@dataclass(frozen=True)
class ExternalItemSpec:
    position_id: str
    kind: ExternalItemKind
    product_description: str
    width_mm: int
    height_mm: int
    quantity: int = 1
    supplier: str | None = None
    supplier_model: str | None = None
    components: tuple[ExternalComponent, ...] = ()
    illustration: ReferenceImage | None = None
    # Only a *complete total* explicitly approved by a salesperson may
    # populate the price field. Online comparables cannot be passed here.
    approved_total_unit_price: str | None = None
    approved_price_source: str | None = None
    explicit_salesperson_price_approval: bool = False
    currency: str = "PLN"

    def __post_init__(self):
        if not self.position_id.strip() or not self.product_description.strip():
            raise ValueError("external_item_identity_required")
        if not isinstance(self.kind, ExternalItemKind):
            raise ValueError("external_item_kind_required")
        if any(type(v) is not int or v <= 0 for v in (
            self.width_mm, self.height_mm, self.quantity,
        )):
            raise ValueError("external_item_dimensions_required")
        if not self.currency.isalpha() or len(self.currency) != 3:
            raise ValueError("invalid_currency")
        if self.supplier_model and not self.supplier:
            raise ValueError("model_needs_supplier")
        if self.approved_total_unit_price is not None:
            _check_price(self.approved_total_unit_price)
            if not (self.explicit_salesperson_price_approval
                    and isinstance(self.approved_price_source, str)
                    and self.approved_price_source.strip()):
                raise ValueError("approved_total_requires_salesperson_and_provenance")
        elif self.explicit_salesperson_price_approval:
            raise ValueError("approval_without_total_price")
        if len({c.name.casefold() for c in self.components}) != len(self.components):
            raise ValueError("duplicate_component")


def _check_price(value: str) -> None:
    if not isinstance(value, str):
        raise ValueError("invalid_price")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid_price") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("invalid_price")


@dataclass(frozen=True)
class ExternalDraft:
    task: PositionTask
    state: PriceState
    missing: tuple[str, ...]
    components: tuple[ExternalComponent, ...]
    display_image_is_representative: bool
    exact_catalogue_product_verified: bool = False
    research_performed: bool = False


def build_external_draft(spec: ExternalItemSpec) -> ExternalDraft:
    """Convert non-catalogue product into current mission task.

    Only possible editing path is a descriptive / placeholder position.
    Geometry displayed by actual WindowHub is selected *later* by the
    existing capabilities planner. Source requested dimensions remain
    explicitly distinguished from substituted catalogue geometry.
    """
    description = [
        spec.product_description.strip(),
        f"Produkt spoza zweryfikowanego katalogu WindowHub: {spec.kind.value}.",
        f"Wymiary zamawiane: {spec.width_mm} × {spec.height_mm} mm.",
    ]
    if spec.supplier:
        description.append(f"Dostawca wskazany w zapytaniu: {spec.supplier.strip()}.")
    if spec.supplier_model:
        description.append(f"Model wskazany w zapytaniu: {spec.supplier_model.strip()}.")
    for component in spec.components:
        description.append(f"Element zestawu: {component.name.strip()} ({component.source.strip()}).")

    missing = []
    if spec.approved_total_unit_price is None:
        missing.append("total_unit_price_not_approved")
        if any(c.verified_component_price is not None for c in spec.components):
            state = PriceState.COMPONENT_ONLY
            missing.append("component_prices_are_not_assembly_total")
        else:
            state = PriceState.UNKNOWN
    else:
        state = PriceState.APPROVED_TOTAL

    image = spec.illustration
    allow_image = bool(image and image.use_authorized)
    if image:
        description.append(
            "Ilustracja " + ("poglądowa" if image.representative_only else "produktu wg źródła")
            + f": {image.description.strip()} (źródło: {image.source.strip()})."
        )
        if not allow_image:
            missing.append("illustration_use_not_authorized_not_inserted")
    else:
        missing.append("illustration_not_supplied_optional")
    if state != PriceState.APPROVED_TOTAL:
        description.append("Cena całkowita: NIEUSTALONA — do wyceny przez handlowca.")
    description.append("Przed ofertą końcową sprawdzić produkt i warunki techniczne u dostawcy.")

    task = PositionTask(
        position_id=spec.position_id,
        request=QuoteRequest(
            description="\n".join(description),
            quantity=spec.quantity,
            requested_width_mm=spec.width_mm,
            requested_height_mm=spec.height_mm,
            manual_unit_price=spec.approved_total_unit_price,
            currency=spec.currency,
            image_reference=image.path_or_reference if allow_image else None,
            image_use_authorized=allow_image,
            allow_placeholder=True,
            force_non_catalogue=True,
        ),
        technical=TechnicalFinding(
            TechnicalStatus.NOT_CHECKED,
            "Produkt zewnętrzny — parametry i gwarancja wymagają kontroli.",
        ),
        allow_unpriced_draft=True,
    )
    return ExternalDraft(
        task=task,
        state=state,
        missing=tuple(missing),
        components=spec.components,
        display_image_is_representative=bool(image and image.representative_only),
    )
