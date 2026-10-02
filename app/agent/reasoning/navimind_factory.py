from __future__ import annotations

from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)
from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)
from app.agent.execution.default_executors import (
    create_default_executor_registry,
)
from app.agent.execution.execution_engine import (
    ExecutionEngine,
)
from app.agent.execution.executor_registry import (
    ExecutorRegistry,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.perception.perception_provider import (
    PerceptionProvider,
)
from app.agent.reasoning.navimind_client import (
    NaviMindClient,
)
from app.agent.reasoning.navimind_config import (
    NaviMindConfig,
)
from app.agent.reasoning.navimind_loop import (
    NaviMindAgentLoop,
)
from app.agent.reasoning.navimind_executor import (
    NaviMindSemanticActionExecutor,
)


def create_navimind_agent_loop(
    *,
    environment: EnvironmentAdapter,
    perception_providers: tuple[
        PerceptionProvider, ...
    ] = (),
    config: NaviMindConfig | None = None,
    executor_registry: ExecutorRegistry | None = None,
    max_steps: int = 12,
) -> NaviMindAgentLoop:
    registry = (
        executor_registry
        if executor_registry is not None
        else create_default_executor_registry()
    )

    if not any(
        isinstance(
            executor,
            NaviMindSemanticActionExecutor,
        )
        for executor in registry.all()
    ):
        registry.register(
            NaviMindSemanticActionExecutor()
        )

    engine = ExecutionEngine(
        registry=registry
    )

    client = None

    resolved_config = (
        config
        if config is not None
        else NaviMindConfig.from_environment()
    )

    if resolved_config is not None:
        client = NaviMindClient(
            resolved_config
        )

    return NaviMindAgentLoop(
        environment=EnvironmentRuntime(
            adapter=environment
        ),
        perception_engine=PerceptionEngine(
            providers=perception_providers
        ),
        execution_engine=engine,
        client=client,
        config=resolved_config,
        max_steps=max_steps,
    )
