from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


@dataclass
class RecoveryLearningRecord:

    reason: str

    strategy: AlternativeStrategy

    occurrences: int = 1