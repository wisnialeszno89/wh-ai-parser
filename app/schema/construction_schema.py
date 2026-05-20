from dataclasses import (
    dataclass,
    field
)

from app.models.enums import (
    ConstructionCategory,
    OpeningType,
    SegmentKind
)


@dataclass
class Segment:

    kind: SegmentKind

    opening: OpeningType | None = None

    width_mm: int | None = None

    height_mm: int | None = None

    is_active: bool = False

    has_handle: bool = False


@dataclass
class ConstructionSchema:

    category: ConstructionCategory

    width_mm: int

    height_mm: int

    profile_system: str

    glass_type: str

    color_inside: str

    color_outside: str

    segments: list[Segment] = field(
        default_factory=list
    )

    addons: list[str] = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )

    roller_shutter: bool = False

    mosquito_net: bool = False

    sill: bool = False

    garage_gate: bool = False

    annotations: list[str] = field(
        default_factory=list
    )