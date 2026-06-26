from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.failure_pattern import (
    FailurePattern
)


@dataclass
class FailurePatternResult:

    patterns: list[FailurePattern]