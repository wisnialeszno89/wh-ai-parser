from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.pattern_frequency import (
    PatternFrequency
)


@dataclass
class PatternMiningResult:

    patterns: list[PatternFrequency]