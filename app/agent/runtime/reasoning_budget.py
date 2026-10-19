from dataclasses import dataclass


@dataclass
class ReasoningBudget:
    """Local hard limit for expensive semantic reasoning calls."""

    max_calls: int
    calls: int = 0

    def __post_init__(self) -> None:
        if self.max_calls < 1:
            raise ValueError(
                "max_calls must be at least 1."
            )

    @property
    def remaining(self) -> int:
        return max(self.max_calls - self.calls, 0)

    @property
    def exhausted(self) -> bool:
        return self.calls >= self.max_calls

    def consume(self) -> bool:
        """Reserve one reasoning call without consulting the model."""
        if self.exhausted:
            return False

        self.calls += 1
        return True
