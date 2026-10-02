from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)


class ExplodingSafetyGate:
    def can_execute(self, tracked_object, action):
        raise AssertionError("SafetyGate must not be called")


class ExplodingBridge:
    def resolve(self, tracked_object, root):
        raise AssertionError("Bridge must not be called")


class ExplodingMouse:
    def click(self, x, y):
        raise AssertionError("Mouse must not be called")


def test_action_policy_rejects_before_safety_gate_bridge_and_mouse():
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        safety_gate=ExplodingSafetyGate(),
        bridge=ExplodingBridge(),
        mouse=ExplodingMouse(),
    )

    result = executor.execute(
        tracked_object=None,
        action=InteractionAction.DOUBLE_CLICK,
        root=None,
    )

    assert result.success is False
    assert result.executed is False
    assert result.action is InteractionAction.DOUBLE_CLICK
    assert result.mode is RobotExecutionMode.DRY_RUN
    assert result.reason == "Action policy rejected action"
