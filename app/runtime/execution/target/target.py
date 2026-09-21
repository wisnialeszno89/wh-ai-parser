from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Target:
    """Resolved screen target used by interaction executors."""

    x: int
    y: int
