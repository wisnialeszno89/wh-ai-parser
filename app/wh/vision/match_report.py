from dataclasses import dataclass


@dataclass
class MatchReport:

    normal: float

    gray: float

    multiscale: float

    winner: str