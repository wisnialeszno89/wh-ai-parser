from dataclasses import dataclass

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement

from app.runtime.execution.robot_action_executor import RobotActionExecutor
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


@dataclass
class FakeObservation:
    source: str = "robot_gui_executor_test"


class TestRobotGUIExecutor:
    def test_click_screen_element_reaches_robot_mouse_dry_run(self):
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
            id="TO-TEST-0001",
            object=logical_object,
            control_type=ControlType.BUTTON,
            confidence=1.0,
            first_seen=1.0,
            last_seen=1.0,
            observation_count=2,
            consecutive_observations=2,
            consecutive_missed_frames=0,
            status=TrackedObjectStatus.STABLE,
            stability=1.0,
        )

        gui_object = GUIObject(
            id="GUI-TEST-0001",
            type=ControlType.BUTTON,
            bounds=bounds,
        )

        element = ScreenElement(
            kind=ControlType.BUTTON.value,
            label="TO-TEST-0001",
            x=bounds.x,
            y=bounds.y,
            width=bounds.width,
            height=bounds.height,
            confidence=1.0,
            metadata={
                "tracked_object_id": tracked_object.id,
                "control_type": ControlType.BUTTON.value,
                "status": TrackedObjectStatus.STABLE.value,
                "stability": 1.0,
                "consecutive_observations": 2,
            },
        )

        scene = ScreenScene(
            observation=FakeObservation(),
            elements=(element,),
            metadata={
                "vision_source": "test",
                "tracked_object_count": 1,
            },
        )

        request = AgentRequest(
            message="Kliknij przycisk testowy.",
            session_id="robot-gui-test",
            salesman_id="test",
            metadata={},
        )

        context = ExecutionContext(
            request=request,
            current_scene=scene,
        )

        context.set_value(
            "robot_target_id",
            tracked_object.id,
        )
        context.set_value(
            "robot_tracked_objects",
            (tracked_object,),
        )
        context.set_value(
            "gui_object_root",
            gui_object,
        )

        executor = RobotGUIExecutor(
            RobotActionExecutor(
                mouse=RobotMouse(
                    mode=RobotMouseMode.DRY_RUN,
                )
            )
        )

        action = AgentAction(
            name="click_screen_element",
            description="Kliknij element TO-TEST-0001",
        )

        result = executor.execute(
            action,
            context,
        )

        assert result.success is True
        assert result.requires_manual_review is False
        assert result.metadata is not None
        assert result.metadata["target_id"] == "TO-TEST-0001"
        assert result.metadata["executed"] is False
        assert result.metadata["point"] == (160, 120)
        assert result.metadata["control_type"] == ControlType.BUTTON.value
