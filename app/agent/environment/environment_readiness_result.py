from dataclasses import dataclass

from app.agent.environment.environment_readiness import (
    EnvironmentReadiness,
)


@dataclass(frozen=True)
class EnvironmentReadinessResult:
    """
    Result of evaluating whether the current environment
    satisfies a required environment state.
    """

    readiness: EnvironmentReadiness

    reason: str = ""

    target_application: str | None = None

    target_window_title: str | None = None

    requires_manual_intervention: bool = False

    @property
    def is_ready(self) -> bool:
        return (
            self.readiness
            == EnvironmentReadiness.READY
        )
