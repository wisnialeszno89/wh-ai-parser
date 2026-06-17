from dataclasses import dataclass


@dataclass
class ScreenObject:

    name: str

    x: int

    y: int

    width: int

    height: int

    confidence: float