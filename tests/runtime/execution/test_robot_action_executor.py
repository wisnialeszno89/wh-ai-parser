from dataclasses import dataclass

from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.robot_mouse import (
    RobotMouseMode,
    RobotMouseResult,
)


@dataclass
class FakeBounds:
    x: int
    y: int
    width: int
    height: int


@dataclass
class FakeTarget:
    id: str
    bounds: FakeBounds


class FakeBridge:
    def resolve(self, tracked_object, root):
        return FakeTarget(
            id="button-001",
            bounds=FakeBounds(
                x=100,
                y=200,
                width=20,
                height=10,
            ),
        )


class FakeTrackedObject:
    confidence = 0.91

    class Object:
        id = "tracked-001"

    object = Object()


class AllowClickGate:
    def can_execute(self, tracked_object, action):
        return action is InteractionAction.CLICK


class FakeLiveMouse:
    def __init__(self):
        self.calls = []

    def click(self, x, y):
        self.calls.append((x, y))
        return RobotMouseResult(
            success=True,
            executed=True,
            mode=RobotMouseMode.LIVE,
            point=(x, y),
            reason="Fake LIVE mouse execution",
        )


def test_robot_action_executor_routes_click_to_robot_mouse():
    from app.runtime.execution.robot_mouse import (
        RobotMouse,
    )

    mouse = RobotMouse(mode=RobotMouseMode.DRY_RUN)

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        safety_gate=AllowClickGate(),
        bridge=FakeBridge(),
        mouse=mouse,
    )

    result = executor.execute(
        tracked_object=FakeTrackedObject(),
        action=InteractionAction.CLICK,
        root=object(),
    )

    assert result.success is True
    assert result.executed is False
    assert result.mode is RobotExecutionMode.DRY_RUN
    assert result.target_id == "button-001"
    assert result.point == (110, 205)
    assert result.confidence == 0.91
    assert "hardware not touched" in result.reason


def test_robot_action_executor_live_path_does_not_touch_hardware():
    mouse = FakeLiveMouse()

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=AllowClickGate(),
        bridge=FakeBridge(),
        mouse=mouse,
    )

    result = executor.execute(
        tracked_object=FakeTrackedObject(),
        action=InteractionAction.CLICK,
        root=object(),
        screen_origin=(1000, 700),
    )

    assert result.success is True
    assert result.executed is True
    assert result.mode is RobotExecutionMode.LIVE
    assert result.target_id == "button-001"
    assert result.point == (1110, 905)
    assert mouse.calls == [(1110, 905)]
    assert result.reason == "Fake LIVE mouse execution"
