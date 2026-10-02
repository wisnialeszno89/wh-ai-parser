from dataclasses import dataclass

from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode


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


def test_robot_action_executor_routes_click_to_robot_mouse():
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
