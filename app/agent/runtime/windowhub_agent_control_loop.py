import os

from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.execution.robot_gui_executor import (
    RobotGUIExecutor,
)

from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)

from app.agent.execution.default_executors import (
    create_default_executor_registry,
)

from app.agent.runtime.agent_control_loop import (
    AgentControlLoop,
)

from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)

from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)

from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)

from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)


def create_windowhub_agent_control_loop() -> AgentControlLoop:
    """
    Create the Universal Agent Core control loop
    configured for the WindowHub environment.
    """

    environment = WindowHubEnvironmentAdapter()

    perception_provider = WindowHubVisionProvider()

    execution_mode = (
        RobotExecutionMode.LIVE
        if os.environ.get("WH_REAL_WINDOWHUB") == "1"
        else RobotExecutionMode.DRY_RUN
    )

    robot_gui_executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=execution_mode,
        )
    )

    registry = create_default_executor_registry(
        additional_executors=(robot_gui_executor,),
    )

    execution_engine = ExecutionEngine(
        registry=registry
    )

    return create_default_agent_control_loop(
        environment=environment,
        execution_engine=execution_engine,
        perception_providers=(
            perception_provider,
            WindowHubUIAutomationProvider(),
        ),
    )
