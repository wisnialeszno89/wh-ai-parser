from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.features.profile_package import (
    ProfilePackage
)

from app.wh.runtime.features.glass_package import (
    GlassPackage
)

from app.wh.runtime.features.security_package import (
    SecurityPackage
)

from app.wh.runtime.features.hardware_package import (
    HardwarePackage
)

from app.wh.runtime.features.accessory_package import (
    AccessoryPackage
)


@dataclass
class ConstructionOffer:

    color_inside: str = ""

    color_outside: str = ""

    profile: ProfilePackage = field(

        default_factory=ProfilePackage

    )

    glass: GlassPackage = field(

        default_factory=GlassPackage

    )

    security: SecurityPackage = field(

        default_factory=SecurityPackage

    )

    hardware: HardwarePackage = field(

        default_factory=HardwarePackage

    )

    accessories: AccessoryPackage = field(

        default_factory=AccessoryPackage

    )