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
from app.runtime.execution.vision.bridges.execution_safety_gate import (
    ExecutionSafetyGate,
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


class _ForegroundChangingGate:
    def __init__(self, actual_foreground_handle):
        self.actual_foreground_handle = actual_foreground_handle
        self.calls = []

    def can_activate_window(self, **kwargs):
        self.calls.append(kwargs)
        return (
            kwargs.get("expected_foreground_handle")
            == self.actual_foreground_handle
        )


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
        expected_foreground_handle=501,
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
        expected_foreground_handle=501,
        observed_window_handles=(501, 777),
    )

    assert result.success is True
    assert result.executed is True
    assert activator.calls == [777]
    assert gate.calls == [{
        "window_handle": 777,
        "expected_foreground_handle": 501,
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
        expected_foreground_handle=501,
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
        expected_foreground_handle=501,
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
    context.set_value(
        "_computer_use_v2_window_activation_binding",
        {
            "window_handle": 777,
            "foreground_window_handle": 501,
            "target_ref": "ent_0002",
            "label": "Inbox - Outlook — OUTLOOK.EXE",
        },
    )

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
        "expected_foreground_handle": 501,
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
    context.set_value(
        "_computer_use_v2_window_activation_binding",
        {
            "window_handle": 501,
            "foreground_window_handle": 501,
            "target_ref": "ent_0001",
            "label": "Workbook - Excel — EXCEL.EXE",
        },
    )

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


def test_robot_gui_executor_rejects_activation_without_v2_local_binding():
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
        ),
        context,
    )

    assert result.success is False
    assert calls == []


def test_robot_action_executor_rejects_boolean_window_handle():
    gate = _SafetyGate()
    activator = _WindowActivator()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        window_activator=activator,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_window_activation(
        window_handle=True,
        expected_foreground_handle=1,
        observed_window_handles=(1,),
    )

    assert result.success is False
    assert result.executed is False
    assert gate.calls == []
    assert activator.calls == []


def test_windows_safety_gate_rejects_unobserved_or_boolean_window_handles():
    gate = ExecutionSafetyGate()

    assert gate.can_activate_window(
        window_handle=777,
        expected_foreground_handle=501,
        observed_window_handles=(501,),
    ) is False
    assert gate.can_activate_window(
        window_handle=True,
        expected_foreground_handle=501,
        observed_window_handles=(True, 501),
    ) is False


def test_live_window_activation_fails_closed_when_foreground_guard_rejects_stale_snapshot():
    # The observed foreground was 501, but Windows now reports 900.
    gate = _ForegroundChangingGate(actual_foreground_handle=900)
    activator = _WindowActivator()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        window_activator=activator,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_window_activation(
        window_handle=777,
        expected_foreground_handle=501,
        observed_window_handles=(501, 777),
    )

    assert result.success is False
    assert result.executed is False
    assert gate.calls == [{
        "window_handle": 777,
        "expected_foreground_handle": 501,
        "observed_window_handles": (501, 777),
    }]
    assert activator.calls == []

def test_windows_safety_gate_rejects_target_equal_to_expected_foreground():
    gate = ExecutionSafetyGate()

    assert gate.can_activate_window(
        window_handle=501,
        expected_foreground_handle=501,
        observed_window_handles=(501, 777),
    ) is False
