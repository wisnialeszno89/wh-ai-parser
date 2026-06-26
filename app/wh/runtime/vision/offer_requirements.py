from dataclasses import dataclass


@dataclass(slots=True)
class OfferRequirements:

    windows: int = 0

    balcony_doors: int = 0

    entrance_doors: int = 0

    outside_color: str = ""

    inside_color: str = ""

    glazing: str = ""

    security: str = ""

    profile: str = ""

    language: str = ""