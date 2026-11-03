from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.action_policy import ActionPolicy
from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)


class _SafetyGate:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.calls = []

    def can_activate_window(self, **kwargs):
        self.calls.append(kwargs)
        return self.allowed


class _WindowActivator:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def __call__(self, window_handle):
        self.calls.append(window_handle)
        return self.result


def test_window_activation_is_in_the_explicit_action_policy():
    assert ActionPolicy().can_execute(InteractionAction.ACTIVATE_WINDOW)


def test_dry_run_window_activation_does_not_call_native_activator():
    gate = _SafetyGate()
    activator = _WindowActivator()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        safety_gate=gate,
        window_activator=activator,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_window_activation(
        window_handle=777,
        observed_window_handles=(501, 777),
    )

    assert result.success is True
    assert result.executed is False
    assert result.action is InteractionAction.ACTIVATE_WINDOW
    assert activator.calls == []
    assert gate.calls == []


def test_live_window_activation_requires_current_inventory_and_gate():
    gate = _SafetyGate(allowed=True)
    activator = _WindowActivator(result=True)
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        window_activator=activator,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_window_activation(
        window_handle=777,
        observed_window_handles=(501, 777),
    )

    assert result.success is True
    assert result.executed is True
    assert activator.calls == [777]
    assert gate.calls == [{
        "window_handle": 777,
        "observed_window_handles": (501, 777),
    }]


def test_live_window_activation_rejects_unobserved_handle_before_native_call():
    gate = _SafetyGate(allowed=True)
    activator = _WindowActivator()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        window_activator=activator,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_window_activation(
        window_handle=999,
        observed_window_handles=(501, 777),
    )

    assert result.success is False
    assert result.executed is False
    assert activator.calls == []
    assert gate.calls == []


def test_live_window_activation_fails_closed_when_safety_gate_rejects():
    gate = _SafetyGate(allowed=False)
    activator = _WindowActivator()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        window_activator=activator,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_window_activation(
        window_handle=777,
        observed_window_handles=(501, 777),
    )

    assert result.success is False
    assert result.executed is False
    assert activator.calls == []


def test_robot_gui_executor_routes_only_locally_bound_window_handle():
    calls = []

    class FakeRobotExecutor:
        def execute_window_activation(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                success=True,
                executed=True,
                reason="foreground window confirmed",
            )

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="EXCEL.EXE",
            active_window_title="Workbook - Excel",
        ),
        metadata={
            "window_handle": 501,
            "foreground_window_handle": 501,
            "desktop_windows": (
                SimpleNamespace(handle=501),
                SimpleNamespace(handle=777),
            ),
        },
    )
    context = ExecutionContext(
        request=AgentRequest(message="Switch to Outlook.")
    )
    context.update_scene(ScreenScene(observation=observation))

    result = RobotGUIExecutor(
        robot_action_executor=FakeRobotExecutor(),
    ).execute(
        AgentAction(
            name="activate_window",
            description="Activate Outlook.",
            target="Inbox - Outlook — OUTLOOK.EXE",
            value="777",
            requires_environment_observation=True,
        ),
        context,
    )

    assert result.success is True
    assert result.metadata["executed"] is True
    assert calls == [{
        "window_handle": 777,
        "observed_window_handles": (501, 777),
    }]


def test_robot_gui_executor_rejects_active_window_activation():
    calls = []

    class FakeRobotExecutor:
        def execute_window_activation(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(success=True, executed=True, reason="unexpected")

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="EXCEL.EXE",
            active_window_title="Workbook - Excel",
        ),
        metadata={
            "window_handle": 501,
            "foreground_window_handle": 501,
            "desktop_windows": (SimpleNamespace(handle=501),),
        },
    )
    context = ExecutionContext(
        request=AgentRequest(message="Activate current window.")
    )
    context.update_scene(ScreenScene(observation=observation))

    result = RobotGUIExecutor(
        robot_action_executor=FakeRobotExecutor(),
    ).execute(
        AgentAction(
            name="activate_window",
            description="Activate Excel again.",
            target="Workbook - Excel — EXCEL.EXE",
            value="501",
        ),
        context,
    )

    assert result.success is False
    assert calls == []
