from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


class ExplodingMouse:
    def click(self, x, y):
        raise AssertionError("RobotMouse must not be called after VERIFY failure")


def _make_changed_button():
    current = GUIObject(
        id="button-current",
        type=ControlType.BUTTON,
        bounds=Rect(
            x=400,
            y=400,
            width=80,
            height=30,
        ),
        confidence=0.95,
    )

    tracked = TrackedObject(
        id="track-verify",
        object=current,
        control_type=ControlType.BUTTON,
        confidence=0.95,
        observation_count=3,
        consecutive_observations=3,
        status=TrackedObjectStatus.STABLE,
        stability=1.0,
    )

    return tracked


def test_verification_failure_blocks_mouse_execution():
    tracked = _make_changed_button()

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        mouse=ExplodingMouse(),
    )

    root = GUIObject(
        id="root",
        type=ControlType.UNKNOWN,
        bounds=Rect(
            x=0,
            y=0,
            width=1000,
            height=1000,
        ),
        children=[tracked.object],
    )

    result = executor.execute(
        tracked_object=tracked,
        action=InteractionAction.CLICK,
        root=root,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(
            x=100,
            y=50,
            width=80,
            height=30,
        ),
    )

    assert result.success is False
    assert result.executed is False
    assert result.target_id == "button-current"
    assert result.point == (440, 415)
    assert "Verification failed" in result.reason
    assert "Target geometry changed" in result.reason

