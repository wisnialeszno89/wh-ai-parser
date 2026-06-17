from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.models.segment import Segment
from app.domain.models.dimension import Dimension
from app.domain.models.mullion import Mullion

from app.domain.enums.construction_type import (
    ConstructionType
)


@dataclass
class Construction:

    construction_type: ConstructionType

    width_mm: int
    height_mm: int

    segments: List[Segment] = field(
        default_factory=list
    )

    mullions: List[Mullion] = field(
        default_factory=list
    )

    dimensions: List[Dimension] = field(
        default_factory=list
    )

    color_inside: Optional[str] = None
    color_outside: Optional[str] = None

    glass_package: Optional[str] = None

    profile_system: Optional[str] = None