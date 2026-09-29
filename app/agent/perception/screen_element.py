from dataclasses import dataclass
from typing import Mapping

from app.agent.perception.interaction_capability import (
    InteractionCapability,
)


@dataclass(frozen=True)
class ScreenElement:
    """
    Semantic representation of a single element visible
    in the observed screen environment.

    Visual type and interaction capability are separate contracts.
    The element remains independent from the technology
    used to detect it.

    It may later originate from:
    - accessibility APIs
    - browser DOM inspection
    - OCR
    - computer vision
    - template matching
    """

    kind: str

    label: str | None = None

    x: int | None = None
    y: int | None = None

    width: int | None = None
    height: int | None = None

    confidence: float | None = None

    metadata: Mapping[str, object] | None = None

    interaction_capability: InteractionCapability = (
        InteractionCapability.UNKNOWN
    )

    @property
    def has_bounds(self) -> bool:
        return all(
            value is not None
            for value in (
                self.x,
                self.y,
                self.width,
                self.height,
            )
        )
