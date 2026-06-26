from dataclasses import (
    dataclass
)


@dataclass
class MetaCognitionInsight:

    total_reflections: int

    total_successes: int

    total_failures: int

    success_rate: float