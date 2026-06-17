from dataclasses import dataclass


@dataclass
class SegmentSemantic:

    opening: str

    operation: str

    role: str

    position: str | None = None

    movable_mullion: bool = False

    door: bool = False