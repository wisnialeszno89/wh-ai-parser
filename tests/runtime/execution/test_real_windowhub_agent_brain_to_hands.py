import os

import pytest

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.perception.robot_vision_perception_engine import (
    RobotVisionPerceptionEngine,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.execution.robot_gui_executor import RobotGUIExecutor

from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.robot_mouse import RobotMouse
from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


class ProbeSafetyGate:
    """
    Test-only gate.

    Allows stable ICON CLICK candidates without changing
    production ICON execution policy.
    """

    def can_execute(self, tracked_object, action):
        return (
            action.value == "click"
            and tracked_object.control_type is not None
            and str(tracked_object.control_type).endswith("ICON")
            and tracked_object.status.value == "stable"
        )


@pytest.mark.integration
def test_real_windowhub_agent_brain_to_robot_hands_dry_run():
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        pytest.skip(
            "Set WH_REAL_WINDOWHUB=1 to run against the real WindowHub"
        )

    pipeline = VisionPipeline()

    # Establish tracker identity and stability.
    pipeline.observe()
    runtime_context = pipeline.observe()

    stable_icons = [
        obj
        for obj in runtime_context.tracked_objects
        if (
            obj.control_type is not None
            and str(obj.control_type).endswith("ICON")
            and obj.status.value == "stable"
        )
    ]

    assert stable_icons, (
        "Expected at least one stable ICON in WindowHub"
    )

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="WindowHub",
        ),
    )

    perception = RobotVisionPerceptionEngine(
        vision_pipeline=pipeline,
    )

    scene = perception.perceive(observation)

    assert scene.elements, (
        "Robot perception should expose WindowHub screen elements"
    )

    robot_action_executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        safety_gate=ProbeSafetyGate(),
        mouse=RobotMouse(),
    )

    robot_gui_executor = RobotGUIExecutor(
        robot_action_executor=robot_action_executor,
    )

    registry = ExecutorRegistry(
        executors=(robot_gui_executor,),
    )

    engine = ExecutionEngine(
        registry=registry,
    )

    request = AgentRequest(
        message="Kliknij element WindowHub.",
        session_id="real-windowhub-agent-test",
        salesman_id="test",
    )

    context = ExecutionContext(
        request=request,
    )

    context.update_observation(observation)
    context.update_scene(scene)

    context.set_value(
        "robot_tracked_objects",
        tuple(runtime_context.tracked_objects),
    )

    context.set_value(
        "gui_object_root",
        runtime_context.scene_graph.root,
    )

    results = []

    for target in stable_icons:
        context.set_value(
            "robot_target_id",
            target.id,
        )

        action = AgentAction(
            name="click_screen_element",
            description=(
                f"Kliknij element {target.id}"
            ),
        )

        result = engine.execute(
            action=action,
            context=context,
        )

        results.append(result)

        assert result.action_name == "click_screen_element"
        assert result.success is True
        assert result.requires_manual_review is False

        assert result.metadata is not None
        assert result.metadata["target_id"] == target.id
        assert result.metadata["executed"] is False
        assert result.metadata["point"] is not None
        assert result.metadata["control_type"] is not None

        assert "hardware not touched" in result.message

    assert len(results) == len(stable_icons)
