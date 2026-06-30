from dataclasses import dataclass

from app.construction.models.opening import (
    Opening
)


@dataclass
class Field:

    opening: Opening

    width: int | None = None

    height: int | None = None

    color: str | None = None

    frame: str | None = None

    glass: str | None = None

    hardware: str | None = None

    extension: str | None = None