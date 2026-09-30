from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
)
from app.runtime.execution.robot_mouse import (
    RobotMouse,
    RobotMouseMode,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)
from app.runtime.execution.vision.models.logical_object import (
    LogicalObject,
)
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


def build_context(
    *,
    capability: InteractionCapability,
    capability_confidence: float,
):
    bounds = Rect(
        x=120,
        y=80,
        width=140,
        height=40,
    )

    logical_object = LogicalObject(
        bounds=bounds,
        root_contour_index=10,
        member_contour_indices=(10, 11),
    )

    tracked_object = TrackedObject(
        id="TO-GATE-0001",
        object=logical_object,
        control_type=ControlType.ICON,
        confidence=0.92,
        observation_count=3,
        consecutive_observations=3,
        status=TrackedObjectStatus.STABLE,
        stability=1.0,
    )

    gui_object = GUIObject(
        id="GUI-GATE-0001",
        type=ControlType.ICON,
        bounds=bounds,
    )

    element = ScreenElement(
        kind="icon",
        label="TO-GATE-0001",
        x=bounds.x,
        y=bounds.y,
        width=bounds.width,
        height=bounds.height,
        confidence=0.92,
        interaction_capability=capability,
        metadata={
            "tracked_object_id": tracked_object.id,
            "semantic_label": "settings",
            "status": "stable",
            "consecutive_observations": 3,
            "interaction_capability_confidence": (
                capability_confidence
            ),
        },
    )

    scene = ScreenScene(
        observation=None,
        elements=(element,),
        metadata={},
    )

    context = ExecutionContext(
        request=AgentRequest(
            message="Kliknij ustawienia.",
        ),
    )

    context.update_scene(scene)
    context.set_value(
        "robot_target",
        "settings",
    )
    context.set_value(
        "robot_tracked_objects",
        (tracked_object,),
    )
    context.set_value(
        "gui_object_root",
        gui_object,
    )

    return context


def create_engine():
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mouse=RobotMouse(
                mode=RobotMouseMode.DRY_RUN,
            ),
        ),
    )

    return ExecutionEngine(
        registry=ExecutorRegistry(
            executors=(executor,),
        ),
    )


def create_action():
    return AgentAction(
        name="click_screen_element",
        description="Kliknij ustawienia.",
    )


def test_production_safety_chain_allows_explicit_clickable_icon_in_dry_run():
    context = build_context(
        capability=InteractionCapability.CLICKABLE,
        capability_confidence=0.99,
    )

    result = create_engine().execute(
        action=create_action(),
        context=context,
    )

    assert result.success is True
    assert result.requires_manual_review is False
    assert result.metadata is not None
    assert result.metadata["target"] == "settings"
    assert result.metadata["target_id"] == "TO-GATE-0001"
    assert result.metadata["control_type"] == "icon"
    assert result.metadata["interaction_capability"] == "clickable"
    assert result.metadata[
        "interaction_capability_confidence"
    ] == 0.99
    assert result.metadata["executed"] is False
    assert result.metadata["point"] == (190, 100)
    assert "hardware not touched" in result.message


def test_production_safety_chain_blocks_icon_without_explicit_capability():
    context = build_context(
        capability=InteractionCapability.UNKNOWN,
        capability_confidence=0.99,
    )

    result = create_engine().execute(
        action=create_action(),
        context=context,
    )

    assert result.success is False
    assert result.requires_manual_review is True
    assert result.metadata is not None
    assert result.metadata["target"] == "settings"


def test_production_safety_chain_blocks_non_interactive_icon():
    context = build_context(
        capability=InteractionCapability.NOT_INTERACTIVE,
        capability_confidence=0.99,
    )

    result = create_engine().execute(
        action=create_action(),
        context=context,
    )

    assert result.success is False
    assert result.requires_manual_review is True


def test_production_safety_chain_blocks_zero_capability_confidence():
    context = build_context(
        capability=InteractionCapability.CLICKABLE,
        capability_confidence=0.0,
    )

    result = create_engine().execute(
        action=create_action(),
        context=context,
    )

    assert result.success is False
    assert result.requires_manual_review is True
