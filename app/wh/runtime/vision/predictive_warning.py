from dataclasses import (
    dataclass
)


@dataclass
class PredictiveWarning:

    reason: str

    confidence: int