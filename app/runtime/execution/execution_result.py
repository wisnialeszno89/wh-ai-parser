from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionResult:
    success: bool
    message: str = ""
    attempts: int = 1
    duration: float = 0.0
    observations: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str = "") -> "ExecutionResult":
        return cls(
            success=True,
            message=message,
        )

    @classmethod
    def fail(cls, message: str) -> "ExecutionResult":
        return cls(
            success=False,
            message=message,
        )