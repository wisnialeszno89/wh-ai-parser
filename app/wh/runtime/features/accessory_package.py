from dataclasses import (
    dataclass
)


@dataclass
class AccessoryPackage:

    roller_shutter: str = ""

    sill: str = ""

    mosquito_net: bool = False

    extension_mm: int = 0

    connector: bool = False