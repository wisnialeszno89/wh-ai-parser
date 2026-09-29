from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.runtime.execution.robot_action_executor import RobotActionExecutor
from app.runtime.execution.robot_mouse import RobotMouse, RobotMouseMode


def test_robot_gui_executor_resolves_semantic_target():
    element = ScreenElement(
        kind="BUTTON",
        label="TO-SEMANTIC-0001",
        x=100,
        y=100,
        width=120,
        height=40,
        confidence=1.0,
        metadata={
            "tracked_object_id": "TO-SEMANTIC-0001",
            "semantic_label": "settings",
            "status": "stable",
            "consecutive_observations": 2,
        },
    )

    scene = ScreenScene(
        observation=None,
        elements=(element,),
    )

    context = ExecutionContext(
        request=AgentRequest(
            message="Kliknij ustawienia.",
            session_id="semantic-target-test",
            salesman_id="test",
        )
    )

    context.update_scene(scene)

    action = AgentAction(
        name="click_screen_element",
        description="Kliknij ustawienia",
    )

    # The semantic target is supplied independently
    # from the AgentAction description.
    context.set_value("robot_target", "settings")

    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mouse=RobotMouse(mode=RobotMouseMode.DRY_RUN),
        )
    )

    registry = ExecutorRegistry(
        executors=(executor,),
    )

    engine = ExecutionEngine(
        registry=registry,
    )

    result = engine.execute(
        action=action,
        context=context,
    )

    assert result.success is False
    assert result.requires_manual_review is True
    assert result.metadata is not None
    assert result.metadata["target"] == "settings"
    assert result.metadata["resolution_score"] == 0.8
