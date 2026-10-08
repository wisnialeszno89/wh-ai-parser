from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.robot_action_executor import RobotActionExecutor
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


class FakeObservation:
    pass


def test_robot_gui_executor_semantic_target_full_dry_run():
    bounds = Rect(
        x=100,
        y=100,
        width=120,
        height=40,
    )

    logical_object = LogicalObject(
        bounds=bounds,
        root_contour_index=100,
        member_contour_indices=(100, 101),
    )

    tracked_object = TrackedObject(
        id="TO-SEMANTIC-0001",
        object=logical_object,
        control_type=ControlType.BUTTON,
        confidence=1.0,
        first_seen=1.0,
        last_seen=2.0,
        observation_count=2,
        consecutive_observations=2,
        consecutive_missed_frames=0,
        status=TrackedObjectStatus.STABLE,
        stability=1.0,
    )

    gui_object = GUIObject(
        id="GUI-SEMANTIC-0001",
        type=ControlType.BUTTON,
        bounds=bounds,
    )

    root = gui_object

    element = ScreenElement(
        kind="BUTTON",
        label="TO-SEMANTIC-0001",
        x=bounds.x,
        y=bounds.y,
        width=bounds.width,
        height=bounds.height,
        confidence=1.0,
        metadata={
            "tracked_object_id": "TO-SEMANTIC-0001",
            "semantic_label": "settings",
            "status": "stable",
            "consecutive_observations": 2,
        },
    )

    scene = ScreenScene(
        observation=FakeObservation(),
        elements=(element,),
    )

    context = ExecutionContext(
        request=AgentRequest(
            message="Kliknij ustawienia.",
            session_id="semantic-full-dry-run",
            salesman_id="test",
        )
    )

    context.update_scene(scene)
    context.set_value(
        "robot_tracked_objects",
        (tracked_object,),
    )
    context.set_value(
        "gui_object_root",
        root,
    )

    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mouse=RobotMouse(
                mode=RobotMouseMode.DRY_RUN,
            ),
        ),
    )

    engine = ExecutionEngine(
        registry=ExecutorRegistry(
            executors=(executor,),
        ),
    )

    action = AgentAction(
        name="click_screen_element",
        description="Kliknij ustawienia",
        target="settings",
    )

    result = engine.execute(
        action=action,
        context=context,
    )

    assert result.success is True
    assert result.requires_manual_review is False

    assert result.metadata is not None
    assert result.metadata["target"] == "settings"
    assert result.metadata["target_id"] == "TO-SEMANTIC-0001"
    assert result.metadata["executed"] is False
    assert result.metadata["point"] == (160, 120)

    assert result.metadata["resolution_score"] == 0.8
    assert result.metadata["control_type"] == "BUTTON"

    assert "hardware not touched" in result.message



def test_robot_gui_executor_uses_guarded_uia_when_tracker_is_not_stable():
    from types import SimpleNamespace

    from app.agent.perception.interaction_capability import (
        InteractionCapability,
    )

    bounds = Rect(
        x=40,
        y=30,
        width=160,
        height=36,
    )

    element = ScreenElement(
        kind="button",
        label="NOWA OFERTA",
        x=bounds.x,
        y=bounds.y,
        width=bounds.width,
        height=bounds.height,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windowhub_ui_automation",
            "provider_element_id": "uia:runtime-1",
            "name": "NOWA OFERTA",
            "uia_runtime_id": "10-20-30",
            "uia_control_type": "button",
            "uia_enabled": True,
            "uia_visible": True,
            "interaction_capability": "clickable",
            "interaction_capability_confidence": 0.99,
        },
    )

    scene = ScreenScene(
        observation=None,
        elements=(element,),
    )

    context = ExecutionContext(
        request=AgentRequest(
            message="Przygotuj nową ofertę.",
            session_id="uia-fallback-test",
        )
    )
    context.update_scene(scene)

    unstable_tracked_object = SimpleNamespace(
        id="TO-UNSTABLE-0001",
        consecutive_observations=1,
    )
    context.set_value(
        "robot_tracked_objects",
        (unstable_tracked_object,),
    )

    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mouse=RobotMouse(
                mode=RobotMouseMode.DRY_RUN,
            ),
        ),
    )

    result = executor.execute(
        action=AgentAction(
            name="click_screen_element",
            description="Kliknij przycisk 'NOWA OFERTA'.",
            target="NOWA OFERTA",
        ),
        context=context,
    )

    assert result.success is True
    assert result.requires_manual_review is False
    assert result.metadata is not None
    assert (
        result.metadata["execution_path"]
        == "uia_fallback_unstable_tracker"
    )
    assert result.metadata["target_id"] == "uia:runtime-1"
