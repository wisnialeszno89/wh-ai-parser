from app.agent.decision.decision_engine import (
    DecisionEngine,
)

from app.agent.environment.default_environment_preparation_loop import (
    create_default_environment_preparation_loop,
)

from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)

from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
)

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.verification_loop import (
    VerificationLoop,
)

from app.agent.verification.expectation_resolver import (
    ExpectationResolver,
)

from app.agent.verification.outcome_verifier import (
    OutcomeVerifier,
)


def create_default_agent_control_loop(
    *,
    environment: EnvironmentAdapter,
    execution_engine: ExecutionEngine,
) -> AgentControlLoop:
    """
    Create a complete default agent control loop.

    The factory wires together the standard safe agent runtime.

    Platform-specific factories may later provide specialised
    implementations for:

    - Windows
    - browser automation
    - simulator environments
    - remote environments
    """

    environment_runtime = (
        EnvironmentRuntime(
            adapter=environment
        )
    )

    perception_engine = (
        PerceptionEngine()
    )

    verification_loop = (
        VerificationLoop(
            execution_engine=execution_engine,
            environment=environment,
            perception_engine=(
                perception_engine
            ),
            expectation_resolver=(
                ExpectationResolver()
            ),
            outcome_verifier=(
                OutcomeVerifier()
            ),
        )
    )

    environment_preparation_loop = (
        create_default_environment_preparation_loop(
            environment=environment
        )
    )

    return AgentControlLoop(
        environment_runtime=(
            environment_runtime
        ),
        perception_engine=(
            perception_engine
        ),
        decision_engine=(
            DecisionEngine()
        ),
        verification_loop=(
            verification_loop
        ),
        environment_preparation_loop=(
            environment_preparation_loop
        ),
    )
