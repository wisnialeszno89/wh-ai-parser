from app.agent.execution.robot_gui_executor import (
    RobotGUIExecutor,
)
from app.agent.runtime.windowhub_agent_control_loop import (
    create_windowhub_agent_control_loop,
)
from app.runtime.execution.robot_action_executor import (
    RobotExecutionMode,
)


def _robot_gui_executor(loop):
    executors = (
        loop.verification_loop
        .execution_engine
        .registry
        .all()
    )

    return next(
        executor
        for executor in executors
        if isinstance(
            executor,
            RobotGUIExecutor,
        )
    )


def test_windowhub_control_loop_defaults_to_dry_run(
    monkeypatch,
):
    monkeypatch.delenv(
        "WH_REAL_WINDOWHUB",
        raising=False,
    )

    loop = create_windowhub_agent_control_loop()
    executor = _robot_gui_executor(loop)

    assert (
        executor.robot_action_executor.mode
        is RobotExecutionMode.DRY_RUN
    )


def test_windowhub_control_loop_requires_explicit_live_opt_in(
    monkeypatch,
):
    monkeypatch.setenv(
        "WH_REAL_WINDOWHUB",
        "1",
    )

    loop = create_windowhub_agent_control_loop()
    executor = _robot_gui_executor(loop)

    assert (
        executor.robot_action_executor.mode
        is RobotExecutionMode.LIVE
    )
