from dataclasses import dataclass

from app.wh.model.opening import (
    Opening
)


@dataclass
class Segment:

    kind: str

    opening: Opening

    width_mm: int | None = None

    height_mm: int | None = None