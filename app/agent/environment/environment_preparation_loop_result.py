from dataclasses import dataclass

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)

from app.agent.environment.environment_readiness_result import (
    EnvironmentReadinessResult,
)


@dataclass(frozen=True)
class EnvironmentPreparationLoopResult:
    """
    Complete result of attempting to ensure that the
    environment satisfies a requirement.

    A successful preparation execution does not itself mean
    that the environment is ready. Readiness must always be
    evaluated again after preparation.
    """

    initial_readiness: EnvironmentReadinessResult

    final_readiness: EnvironmentReadinessResult

    preparation: EnvironmentPreparation | None = None

    execution_result: (
        EnvironmentPreparationResult | None
    ) = None

    @property
    def ready(self) -> bool:
        return self.final_readiness.is_ready

    @property
    def preparation_was_attempted(self) -> bool:
        return self.execution_result is not None
