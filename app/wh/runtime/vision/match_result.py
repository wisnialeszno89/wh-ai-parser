from dataclasses import (
    dataclass
)


@dataclass
class MatchResult:

    found: bool

    x: int = 0

    y: int = 0

    confidence: float = 0.0