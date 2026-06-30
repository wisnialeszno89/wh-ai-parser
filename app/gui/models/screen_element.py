from dataclasses import dataclass


@dataclass
class ScreenElement:

    name: str

    x: int

    y: int

    width: int

    height: int

    confidence: float = 1.0