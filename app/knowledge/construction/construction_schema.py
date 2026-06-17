from dataclasses import dataclass


@dataclass
class ConstructionSchema:

    width_mm: int

    height_mm: int

    segments: list