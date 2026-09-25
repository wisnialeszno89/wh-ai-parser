from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)


def _make_button_tree():
    child = GUIObject(
        id="button-1",
        type=ControlType.BUTTON,
        bounds=Rect(
            x=100,
            y=50,
            width=80,
            height=30,
        ),
        confidence=0.95,
    )

    root = GUIObject(
        id="root",
        type=ControlType.UNKNOWN,
        bounds=Rect(
            x=0,
            y=0,
            width=500,
            height=300,
        ),
        children=[child],
    )

    return root, child


def _make_tracked_button():
    root, child = _make_button_tree()

    tracked = TrackedObject(
        id="track-1",
        object=child,
        control_type=ControlType.BUTTON,
        confidence=0.95,
        observation_count=3,
        consecutive_observations=3,
        status=TrackedObjectStatus.STABLE,
        stability=1.0,
    )

    return root, child, tracked


def test_dry_run_resolves_target_without_touching_hardware():
    from app.runtime.execution.robot_action_executor import (
        RobotActionExecutor,
        RobotExecutionMode,
    )

    root, child, tracked = _make_tracked_button()

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
    )

    result = executor.execute(
        tracked_object=tracked,
        action=InteractionAction.CLICK,
        root=root,
    )

    assert result.success is True
    assert result.executed is False
    assert result.mode is RobotExecutionMode.DRY_RUN
    assert result.target_id == child.id
    assert result.point == (140, 65)
    assert result.confidence == 0.95
    assert "hardware not touched" in result.reason


def test_safety_rejection_never_reaches_target_resolution():
    from app.runtime.execution.robot_action_executor import (
        RobotActionExecutor,
        RobotExecutionMode,
    )

    root, child, tracked = _make_tracked_button()

    tracked.status = TrackedObjectStatus.LOST

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
    )

    result = executor.execute(
        tracked_object=tracked,
        action=InteractionAction.CLICK,
        root=root,
    )

    assert result.success is False
    assert result.executed is False
    assert result.target_id == child.id
    assert result.point is None


def test_unresolved_target_is_rejected():
    from app.runtime.execution.robot_action_executor import (
        RobotActionExecutor,
        RobotExecutionMode,
    )

    root, child, tracked = _make_tracked_button()

    # The tracked object still represents the original button location.
    # The current GUI tree contains a visually unrelated object elsewhere.
    current_object = GUIObject(
        id="different-button",
        type=ControlType.BUTTON,
        bounds=Rect(
            x=1000,
            y=1000,
            width=80,
            height=30,
        ),
        confidence=0.95,
    )

    root.children = [current_object]

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
    )

    result = executor.execute(
        tracked_object=tracked,
        action=InteractionAction.CLICK,
        root=root,
    )

    assert result.success is False
    assert result.executed is False
    assert result.point is None


def test_live_mode_is_explicitly_blocked_for_now():
    from app.runtime.execution.robot_action_executor import (
        RobotActionExecutor,
        RobotExecutionMode,
    )

    root, child, tracked = _make_tracked_button()

    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
    )

    result = executor.execute(
        tracked_object=tracked,
        action=InteractionAction.CLICK,
        root=root,
    )

    assert result.success is False
    assert result.executed is False
    assert result.mode is RobotExecutionMode.LIVE
    assert result.target_id == child.id
    assert result.point == (140, 65)
    assert "LIVE execution is not enabled" in result.reason

