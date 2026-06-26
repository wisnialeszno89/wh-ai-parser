from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


@dataclass
class RecoveryPlan:

    strategy: AlternativeStrategy

    reason: str