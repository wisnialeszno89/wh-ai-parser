from dataclasses import dataclass

from app.agent.offers.profile_selection import ProfileSelectionSource


@dataclass(frozen=True)
class OfferContext:
    """
    Normalized business context extracted from a
    salesman quotation request.

    This model intentionally contains only the
    minimum data required for the first quotation
    workflow.

    More technical and commercial fields can be
    added incrementally as the workflow grows.
    """

    raw_request: str

    width: int | None = None

    height: int | None = None

    quantity: int = 1

    product_type: str | None = None

    profile: str | None = None

    profile_source: ProfileSelectionSource = ProfileSelectionSource.DEFAULT

    configuration: str | None = None

    opening: str | None = None

    openings: tuple[str, ...] = ()

    color_inside: str | None = None

    color_outside: str | None = None

    glazing: str | None = None

    missing_fields: tuple[str, ...] = ()

    conflicts: tuple[str, ...] = ()
