from __future__ import annotations

import os

from app.agent.environment.windows_desktop_environment_adapter import (
    WindowsDesktopEnvironmentAdapter,
)
from app.agent.execution.default_executors import (
    create_default_executor_registry,
)
from app.agent.execution.execution_engine import (
    ExecutionEngine,
)
from app.agent.execution.robot_gui_executor import (
    RobotGUIExecutor,
)
from app.agent.perception.windows_ui_automation_provider import (
    WindowsUIAutomationProvider,
)
from app.agent.reasoning.plan_reasoner import (
    PlanReasoner,
)
from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)
from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)


def create_windows_desktop_agent_control_loop(
    *,
    plan_reasoner: PlanReasoner | None = None,
) -> AgentControlLoop:
    """
    Create the Universal Agent Core configured for generic Windows.

    LIVE execution is explicitly opt-in through COMPUTER_REAL=1.
    Without it, RobotActionExecutor remains in DRY_RUN mode.
    """

    environment = WindowsDesktopEnvironmentAdapter()

    execution_mode = (
        RobotExecutionMode.LIVE
        if os.environ.get("COMPUTER_REAL") == "1"
        else RobotExecutionMode.DRY_RUN
    )

    robot_gui_executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=execution_mode,
        )
    )

    registry = create_default_executor_registry(
        additional_executors=(
            robot_gui_executor,
        ),
    )

    execution_engine = ExecutionEngine(
        registry=registry,
    )

    return create_default_agent_control_loop(
        environment=environment,
        execution_engine=execution_engine,
        perception_providers=(
            WindowsUIAutomationProvider(),
        ),
        plan_reasoner=plan_reasoner,
    )
