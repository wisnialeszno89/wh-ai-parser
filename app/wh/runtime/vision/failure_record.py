from dataclasses import (
    dataclass
)


@dataclass
class FailureRecord:

    goal: str

    reason: str

    recovery_attempts: int = 0