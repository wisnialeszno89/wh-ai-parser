from dataclasses import (
    dataclass
)


@dataclass
class FieldGeometry:

    center_x: int

    center_y: int

    width_ratio: float = 1.0

    height_ratio: float = 1.0