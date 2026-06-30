from dataclasses import dataclass, field

from app.context.context_source import (
    ContextSource
)


@dataclass
class OfferContext:

    customer_name: str | None = None

    profile: str | None = None
    profile_source: ContextSource = (
        ContextSource.DEFAULT
    )

    color: str | None = None
    color_source: ContextSource = (
        ContextSource.DEFAULT
    )

    width: int | None = None
    height: int | None = None

    construction_type: str | None = None

    opening: str | None = None

    confidence: float = 1.0

    manual_review: bool = False

    notes: list[str] = field(
        default_factory=list
    )