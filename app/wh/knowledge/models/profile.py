from dataclasses import dataclass


@dataclass(slots=True)
class Profile:

    manufacturer: str

    system: str

    security: list[str]

    glazing: list[str]

    colors: list[str]