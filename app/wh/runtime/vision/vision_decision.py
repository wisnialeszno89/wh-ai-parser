from dataclasses import (
    dataclass
)


@dataclass
class VisionDecision:

    execute: bool

    reason: str