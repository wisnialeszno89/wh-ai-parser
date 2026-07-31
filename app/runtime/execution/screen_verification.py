from dataclasses import dataclass


@dataclass
class ScreenVerification:

    changed: bool

    difference_score: int