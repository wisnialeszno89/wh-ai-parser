from dataclasses import (
    dataclass
)


@dataclass
class IntelligentVisionExecutionResult:

    success: bool

    message: str = ""