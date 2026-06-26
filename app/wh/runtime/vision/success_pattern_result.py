from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.success_pattern import (
    SuccessPattern
)


@dataclass
class SuccessPatternResult:

    patterns: list[SuccessPattern]