from dataclasses import (
    dataclass
)


@dataclass
class Segment:

    opening: str

    width_ratio: float = 1.0

    height_ratio: float = 1.0