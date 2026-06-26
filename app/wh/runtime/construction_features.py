from dataclasses import (
    dataclass
)


@dataclass
class ConstructionFeatures:

    color_inside: str = ""

    color_outside: str = ""

    glass: str = "2glass"

    warm_edge: bool = False

    swisspacer: bool = False

    v_perfect: bool = False

    hidden_hinges: bool = False

    contacts: bool = False

    security_glass_p4: bool = False

    security_class_rc2: bool = False

    glass_package_mm: int = 24