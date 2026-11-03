from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)


class _Keyboard:
    def __init__(self):
        self.pressed = []
        self.hotkeys = []

    def press(self, key):
        self.pressed.append(key)

    def hotkey(self, *keys):
        self.hotkeys.append(keys)


class _SafetyGate:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.calls = []

    def can_execute_keyboard_input(self, **kwargs):
        self.calls.append(kwargs)
        return self.allowed


def test_dry_run_keyboard_input_never_touches_hardware():
    keyboard = _Keyboard()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        keyboard=keyboard,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_keyboard_input(
        sequence="alt+tab",
        window_handle=501,
    )

    assert result.success is True
    assert result.executed is False
    assert result.action is InteractionAction.KEY_PRESS
    assert keyboard.pressed == []
    assert keyboard.hotkeys == []


def test_live_keyboard_input_uses_allowlisted_shortcut_and_foreground_gate():
    keyboard = _Keyboard()
    gate = _SafetyGate(allowed=True)
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        keyboard=keyboard,
        mouse=SimpleNamespace(),
        safety_gate=gate,
    )

    result = executor.execute_keyboard_input(
        sequence="alt+tab",
        window_handle=501,
    )

    assert result.success is True
    assert result.executed is True
    assert keyboard.hotkeys == [("alt", "tab")]
    assert gate.calls == [{
        "window_handle": 501,
        "require_foreground": True,
    }]


def test_live_keyboard_input_fails_closed_when_foreground_gate_rejects():
    keyboard = _Keyboard()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        keyboard=keyboard,
        mouse=SimpleNamespace(),
        safety_gate=_SafetyGate(allowed=False),
    )

    result = executor.execute_keyboard_input(
        sequence="alt+tab",
        window_handle=501,
    )

    assert result.success is False
    assert result.executed is False
    assert keyboard.hotkeys == []


def test_robot_action_executor_rejects_unapproved_shortcut_before_input():
    keyboard = _Keyboard()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        keyboard=keyboard,
        mouse=SimpleNamespace(),
    )

    result = executor.execute_keyboard_input(
        sequence="alt+f4",
        window_handle=501,
    )

    assert result.success is False
    assert result.executed is False
    assert keyboard.hotkeys == []


def test_robot_gui_executor_routes_semantic_press_key_to_global_keyboard():
    calls = []

    class FakeRobotExecutor:
        def execute_keyboard_input(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                success=True,
                executed=True,
                reason="keyboard sequence executed",
            )

    context = ExecutionContext(
        request=AgentRequest(message="Switch to the other application.")
    )
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="EXCEL.EXE",
            active_window_title="Workbook",
        ),
        metadata={"window_handle": 501},
    )
    context.update_scene(
        ScreenScene(
            observation=observation,
            elements=(),
        )
    )
    result = RobotGUIExecutor(
        robot_action_executor=FakeRobotExecutor(),
    ).execute(
        AgentAction(
            name="press_key",
            description="Switch to the next application.",
            target=None,
            value="alt+tab",
            requires_environment_observation=True,
        ),
        context,
    )

    assert result.success is True
    assert result.metadata["executed"] is True
    assert calls == [{
        "sequence": "alt+tab",
        "window_handle": 501,
    }]
