from dataclasses import (
    dataclass
)


@dataclass
class LearningRecord:

    key: str

    value: str

    occurrences: int = 1