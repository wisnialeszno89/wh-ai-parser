from dataclasses import (
    dataclass
)


@dataclass
class FailureLearningRecord:

    failure_reason: str

    recovery_strategy: str

    successful: bool