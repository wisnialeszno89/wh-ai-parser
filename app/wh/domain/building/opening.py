from dataclasses import dataclass


@dataclass
class Opening:

    id: str = ""

    kind: str = ""

    width: int = 0

    height: int = 0

    quantity: int = 1

    room: str = ""