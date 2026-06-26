from dataclasses import dataclass


@dataclass(slots=True)
class WindowProduct:

    quantity: int = 1

    width: int = 0

    height: int = 0

    profile: str = ""

    outside_color: str = ""

    inside_color: str = ""

    glazing: str = ""

    hardware: str = ""

    security: str = ""

    opening_type: str = ""