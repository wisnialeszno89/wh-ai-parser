from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


@dataclass
class RecoveryExecutionResult:

    success: bool

    strategy: AlternativeStrategy