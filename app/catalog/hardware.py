from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareProduct:
    code: str
    manufacturer: str
    system: str
    variant: str = ""


HARDWARE_CATALOG = {
    "WINKHAUS_PRO": HardwareProduct(
        code="WINKHAUS_PRO",
        manufacturer="Winkhaus",
        system="activPilot Concept",
        variant="GAM/GAMA Z",
    ),
}
