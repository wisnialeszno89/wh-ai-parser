from dataclasses import dataclass


@dataclass
class ActionResult:

    success: bool

    message: str = ""

    confidence: float = 0.0