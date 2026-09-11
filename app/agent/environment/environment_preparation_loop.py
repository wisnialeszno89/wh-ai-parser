from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_preparation_executor import (
    EnvironmentPreparationExecutor,
)

from app.agent.environment.environment_preparation_loop_result import (
    EnvironmentPreparationLoopResult,
)

from app.agent.environment.environment_readiness_evaluator import (
    EnvironmentReadinessEvaluator,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)


class EnvironmentPreparationLoop:
    """
    Ensures that the environment is ready before execution.

    Flow:

        observe
        -> evaluate readiness
        -> prepare if required
        -> execute preparation
        -> observe again
        -> evaluate readiness again

    The loop never assumes that preparation succeeded merely
    because the executor reported success.
    """

    def __init__(
        self,
        *,
        environment: EnvironmentAdapter,
        readiness_evaluator: (
            EnvironmentReadinessEvaluator
        ),
        preparation_engine: (
            EnvironmentPreparationEngine
        ),
        preparation_executor: (
            EnvironmentPreparationExecutor
        ),
    ) -> None:

        self.environment = environment

        self.readiness_evaluator = (
            readiness_evaluator
        )

        self.preparation_engine = (
            preparation_engine
        )

        self.preparation_executor = (
            preparation_executor
        )

    def ensure_ready(
        self,
        requirement: EnvironmentRequirement,
    ) -> EnvironmentPreparationLoopResult:
        """
        Ensure that the current environment satisfies the
        supplied requirement.
        """

        initial_observation = (
            self.environment.observe()
        )

        initial_readiness = (
            self.readiness_evaluator.evaluate(
                requirement,
                initial_observation,
            )
        )

        if initial_readiness.is_ready:
            return EnvironmentPreparationLoopResult(
                initial_readiness=initial_readiness,
                final_readiness=initial_readiness,
            )

        preparation = (
            self.preparation_engine.prepare(
                requirement,
                initial_readiness,
            )
        )

        execution_result = (
            self.preparation_executor.execute(
                preparation
            )
        )

        if not execution_result.success:
            return EnvironmentPreparationLoopResult(
                initial_readiness=initial_readiness,
                final_readiness=initial_readiness,
                preparation=preparation,
                execution_result=execution_result,
            )

        final_observation = (
            self.environment.observe()
        )

        final_readiness = (
            self.readiness_evaluator.evaluate(
                requirement,
                final_observation,
            )
        )

        return EnvironmentPreparationLoopResult(
            initial_readiness=initial_readiness,
            final_readiness=final_readiness,
            preparation=preparation,
            execution_result=execution_result,
        )
