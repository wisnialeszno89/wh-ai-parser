from dataclasses import dataclass


@dataclass(slots=True)
class Decision:

    profile: str | None = None

    hardware: str | None = None

    glazing: str | None = None

    confidence: float = 0.0

    explanation: str = ""