from dataclasses import (
    dataclass
)


@dataclass
class ExecutionRecord:

    goal: str

    success: bool

    reason: str