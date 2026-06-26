from dataclasses import dataclass


@dataclass
class WindowRequirement:

    width: int = 0

    height: int = 0

    quantity: int = 1

    profile: str = ""

    color_inside: str = ""

    color_outside: str = ""

    glazing: str = ""

    hardware: str = ""

    security: str = ""

    opening: str = ""

    room: str = ""