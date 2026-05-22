from dataclasses import dataclass


@dataclass
class WindowIntent:

    geometry: str

    width: int

    height: int

    profile: str | None = None

    glass: str | None = None

    color: str | None = None