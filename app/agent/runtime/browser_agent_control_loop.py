from __future__ import annotations

from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.environment.browser_environment_adapter import (
    BrowserEnvironmentAdapter,
)
from app.agent.execution.default_executors import (
    create_default_executor_registry,
)
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.runtime.agent_control_loop import AgentControlLoop
from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)
from app.agent.reasoning.plan_reasoner import PlanReasoner


def create_browser_agent_control_loop(
    *,
    browser_adapter: BrowserAdapter,
    plan_reasoner: PlanReasoner | None = None,
) -> AgentControlLoop:
    """
    Create the shared AgentControlLoop configured for Browser.

    Browser actions are verified against BrowserPage snapshots rather than
    desktop GUI geometry.
    """

    environment = BrowserEnvironmentAdapter(
        browser_adapter
    )

    execution_engine = ExecutionEngine(
        registry=create_default_executor_registry(
            browser_adapter=browser_adapter,
        )
    )

    return create_default_agent_control_loop(
        environment=environment,
        execution_engine=execution_engine,
        perception_providers=(),
        plan_reasoner=plan_reasoner,
    )
