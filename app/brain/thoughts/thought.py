from dataclasses import dataclass, field


@dataclass
class Thought:

    goal: str

    reasoning: list[str] = field(
        default_factory=list
    )

    decisions: list[str] = field(
        default_factory=list
    )

    confidence: float = 1.0