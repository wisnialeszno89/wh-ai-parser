from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_preparation_executor import (
    EnvironmentPreparationExecutor,
)

from app.agent.environment.environment_preparation_loop import (
    EnvironmentPreparationLoop,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)

from app.agent.environment.environment_readiness_evaluator import (
    EnvironmentReadinessEvaluator,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)


class SequencedEnvironment(
    EnvironmentAdapter
):
    """
    Environment returning observations in sequence.

    Useful for testing environment changes between
    preparation attempts.
    """

    def __init__(
        self,
        observations: tuple[
            EnvironmentObservation,
            ...
        ],
    ) -> None:

        self.observations = observations

        self.observe_count = 0

    def observe(
        self,
    ) -> EnvironmentObservation:

        index = min(
            self.observe_count,
            len(self.observations) - 1,
        )

        self.observe_count += 1

        return self.observations[index]


class RecordingPreparationExecutor(
    EnvironmentPreparationExecutor
):

    def __init__(
        self,
        *,
        success: bool = True,
    ) -> None:

        self.success = success

        self.executed = []

    def execute(
        self,
        preparation,
    ) -> EnvironmentPreparationResult:

        self.executed.append(
            preparation
        )

        return EnvironmentPreparationResult(
            success=self.success,
        )


def create_observation(
    application: str,
) -> EnvironmentObservation:

    return EnvironmentObservation(
        state=EnvironmentState(
            active_application=application,
            active_window_title=(
                f"{application} Window"
            ),
            screen_width=1920,
            screen_height=1080,
        )
    )


def create_requirement():

    return EnvironmentRequirement(
        application="WindowHelper"
    )


def create_loop(
    *,
    observations,
    executor,
):

    return EnvironmentPreparationLoop(
        environment=SequencedEnvironment(
            observations=observations
        ),
        readiness_evaluator=(
            EnvironmentReadinessEvaluator()
        ),
        preparation_engine=(
            EnvironmentPreparationEngine()
        ),
        preparation_executor=executor,
    )


def test_loop_does_not_prepare_ready_environment():

    executor = (
        RecordingPreparationExecutor()
    )

    loop = create_loop(
        observations=(
            create_observation(
                "WindowHelper"
            ),
        ),
        executor=executor,
    )

    result = loop.ensure_ready(
        create_requirement()
    )

    assert result.ready is True

    assert (
        result.preparation_was_attempted
        is False
    )

    assert executor.executed == []


def test_loop_prepares_not_ready_environment():

    executor = (
        RecordingPreparationExecutor()
    )

    loop = create_loop(
        observations=(
            create_observation(
                "OtherApp"
            ),
            create_observation(
                "WindowHelper"
            ),
        ),
        executor=executor,
    )

    result = loop.ensure_ready(
        create_requirement()
    )

    assert result.ready is True

    assert (
        result.preparation_was_attempted
        is True
    )

    assert len(
        executor.executed
    ) == 1


def test_loop_rechecks_environment_after_preparation():

    executor = (
        RecordingPreparationExecutor()
    )

    environment = SequencedEnvironment(
        observations=(
            create_observation(
                "OtherApp"
            ),
            create_observation(
                "WindowHelper"
            ),
        )
    )

    loop = EnvironmentPreparationLoop(
        environment=environment,
        readiness_evaluator=(
            EnvironmentReadinessEvaluator()
        ),
        preparation_engine=(
            EnvironmentPreparationEngine()
        ),
        preparation_executor=executor,
    )

    result = loop.ensure_ready(
        create_requirement()
    )

    assert result.ready is True

    assert (
        environment.observe_count
        == 2
    )


def test_loop_stops_when_preparation_execution_fails():

    executor = (
        RecordingPreparationExecutor(
            success=False
        )
    )

    environment = SequencedEnvironment(
        observations=(
            create_observation(
                "OtherApp"
            ),
            create_observation(
                "WindowHelper"
            ),
        )
    )

    loop = EnvironmentPreparationLoop(
        environment=environment,
        readiness_evaluator=(
            EnvironmentReadinessEvaluator()
        ),
        preparation_engine=(
            EnvironmentPreparationEngine()
        ),
        preparation_executor=executor,
    )

    result = loop.ensure_ready(
        create_requirement()
    )

    assert result.ready is False

    assert (
        result.execution_result.success
        is False
    )

    assert (
        environment.observe_count
        == 1
    )


def test_loop_detects_environment_still_not_ready():

    executor = (
        RecordingPreparationExecutor(
            success=True
        )
    )

    loop = create_loop(
        observations=(
            create_observation(
                "OtherApp"
            ),
            create_observation(
                "StillOtherApp"
            ),
        ),
        executor=executor,
    )

    result = loop.ensure_ready(
        create_requirement()
    )

    assert result.ready is False

    assert (
        result.execution_result.success
        is True
    )

    assert (
        result.initial_readiness.is_ready
        is False
    )

    assert (
        result.final_readiness.is_ready
        is False
    )
