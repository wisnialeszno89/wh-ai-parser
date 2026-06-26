from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


@dataclass
class MetaLearningRecord:

    strategy: AlternativeStrategy

    successes: int = 0