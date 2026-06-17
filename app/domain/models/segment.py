from dataclasses import dataclass
from typing import Optional

from app.domain.enums.opening_type import (
    OpeningType
)


@dataclass
class Segment:

    id: str

    opening_type: OpeningType

    width_mm: Optional[int] = None
    height_mm: Optional[int] = None

    is_active: bool = False

    has_sash: bool = False
    has_glass: bool = False
    has_hardware: bool = False

    glass_type: Optional[str] = None

    color_inside: Optional[str] = None
    color_outside: Optional[str] = None