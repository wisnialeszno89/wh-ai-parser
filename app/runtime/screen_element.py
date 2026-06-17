from dataclasses import dataclass


@dataclass
class ScreenElement:

    name: str

    image: str

    x: int = 0

    y: int = 0