from dataclasses import (
    dataclass
)


@dataclass
class RecoveryKnowledge:

    failure_reason: str

    recovery_strategy: str

    success_count: int

    failure_count: int