from dataclasses import (
    dataclass
)


@dataclass
class FailurePattern:

    pattern: str

    failures: int