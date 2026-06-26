from dataclasses import dataclass


@dataclass
class OfferRequirements:

    windows: int = 0

    doors: int = 0

    color: str = ""

    profile: str = ""

    glazing: str = ""

    hardware: str = ""

    security: str = ""

    installation: bool = False

    transport: bool = False

    language: str = ""

    customer_type: str = ""