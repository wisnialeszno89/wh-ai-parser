from dataclasses import (
    dataclass
)


@dataclass
class ConstructionRequest:

    width: int

    height: int

    notation: str