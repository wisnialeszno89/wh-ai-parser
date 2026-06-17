from dataclasses import dataclass


@dataclass
class Dimension:

    name: str

    value_mm: int

    orientation: str

    editable: bool = True