from dataclasses import (
    dataclass
)


@dataclass
class GlassPackage:

    type: str = "2glass"

    thickness_mm: int = 24

    warm_edge: bool = False

    swisspacer: bool = False

    security_p4: bool = False