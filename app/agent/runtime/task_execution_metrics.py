from dataclasses import dataclass


@dataclass(frozen=True)
class TaskExecutionMetrics:
    """Operational metrics for one autonomous task run."""

    elapsed_seconds: float = 0.0
    cycles: int = 0
    executed_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    confirmations_requested: int = 0

    def __post_init__(self) -> None:
        if self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be non-negative.")

        for field_name in (
            "cycles",
            "executed_actions",
            "successful_actions",
            "failed_actions",
            "confirmations_requested",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(
                    f"{field_name} must be non-negative."
                )

        if self.successful_actions + self.failed_actions > self.executed_actions:
            raise ValueError(
                "successful_actions + failed_actions cannot exceed executed_actions."
            )

    @property
    def actions_per_cycle(self) -> float:
        if self.cycles == 0:
            return 0.0
        return self.executed_actions / self.cycles

    def to_payload(self) -> dict[str, object]:
        return {
            "elapsed_seconds": self.elapsed_seconds,
            "cycles": self.cycles,
            "executed_actions": self.executed_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "confirmations_requested": self.confirmations_requested,
            "actions_per_cycle": self.actions_per_cycle,
        }
