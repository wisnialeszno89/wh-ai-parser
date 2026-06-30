from dataclasses import dataclass
from typing import Any


@dataclass
class IconCandidate:

    x: int
    y: int

    width: int
    height: int

    score: float

    crop: Any

    source_toolbar: Any = None