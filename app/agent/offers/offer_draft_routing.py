"""Route verified, unresolved and unsupported positions in an offer draft."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum


class CatalogStatus(str, Enum):
    SUPPORTED = "supported"
    UNVERIFIED = "unverified"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class DraftPosition:
    reference: str
    description: str
    catalog_status: CatalogStatus
    configuration: Mapping[str, object]
    image_reference: str | None = None


def route_draft_positions(positions: Iterable[DraftPosition]) -> list[dict]:
    """Keep unsupported positions as unpriced manual lines at the end."""
    configurable, review, manual = [], [], []
    for position in positions:
        entry = {"reference": position.reference, "description": position.description}
        if position.catalog_status == CatalogStatus.UNSUPPORTED:
            entry.update(execution="manual", price=None)
            if position.image_reference:
                entry["image_reference"] = position.image_reference
            manual.append(entry)
        elif position.catalog_status == CatalogStatus.SUPPORTED and position.configuration:
            configurable.append(dict(entry, execution="configure", configuration=dict(position.configuration)))
        else:
            review.append(dict(entry, execution="review", configuration=dict(position.configuration)))
    return [*configurable, *review, *manual]
