from dataclasses import (
    dataclass
)


@dataclass
class TopologyCandidate:

    notation: str

    score: float = 0.0

    reason: str = ""