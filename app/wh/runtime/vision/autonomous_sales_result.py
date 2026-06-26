from dataclasses import (
    dataclass
)


@dataclass
class AutonomousSalesResult:

    success: bool

    message: str = ""