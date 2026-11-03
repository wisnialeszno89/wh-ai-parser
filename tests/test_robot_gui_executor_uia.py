from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)


class RecordingMouse:
    def __init__(self):
        self.points = []

    def click(self, x, y):
        point = (int(x), int(y))
        self.points.append(point)
        return SimpleNamespace(
            success=True,
            executed=False,
            point=point,
            reason="recorded dry-run click",
        )


class AllowingUIASafetyGate:
    def can_execute(self, *args, **kwargs):
        return False

    def can_execute_uia_element(self, *args, **kwargs):
        return True


def make_context(
    *,
    elements,
    window_handle=1234,
):
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_window_title="Okna - WindowHub",
        ),
        metadata={
            "window_handle": window_handle,
            "window_rect": SimpleNamespace(
                left=100,
                top=200,
                width=1200,
                height=800,
            ),
        },
    )

    scene = ScreenScene(
        observation=observation,
        elements=tuple(elements),
    )

    return ExecutionContext(
        request=AgentRequest(
            message="Click the button"
        ),
        last_observation=observation,
        current_scene=scene,
    )


def make_uia_element(
    *,
    label="NOWA OFERTA",
    enabled=True,
    visible=True,
    runtime_id="1-2-3",
    automation_id="Nowa_oferta",
    x=20,
    y=30,
):
    return ScreenElement(
        kind="button",
        label=label,
        x=x,
        y=y,
        width=110,
        height=110,
        confidence=0.99,
        interaction_capability=(
            InteractionCapability.CLICKABLE
            if enabled
            else InteractionCapability.NOT_INTERACTIVE
        ),
        metadata={
            "source": "windowhub_ui_automation",
            "provider_element_id": f"uia:{runtime_id}",
            "automation_id": automation_id,
            "uia_control_type": "button",
            "uia_enabled": enabled,
            "uia_visible": visible,
            "uia_runtime_id": runtime_id,
            "interaction_capability": (
                "clickable" if enabled else "not_interactive"
            ),
            "interaction_capability_confidence": 0.99,
        },
    )


def test_robot_gui_executor_clicks_uia_only_target_in_dry_run():
    mouse = RecordingMouse()

    robot = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        mouse=mouse,
    )

    executor = RobotGUIExecutor(
        robot_action_executor=robot,
    )

    context = make_context(
        elements=(make_uia_element(),),
    )

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Click NOWA OFERTA",
            target="NOWA OFERTA",
        ),
        context,
    )

    assert result.success is True
    assert result.requires_manual_review is False
    assert result.metadata["execution_path"] == "uia_only"
    assert result.metadata["target_id"] == "uia:1-2-3"
    assert result.metadata["point"] == (175, 285)
    assert mouse.points == [(175, 285)]


def test_robot_gui_executor_rejects_non_uia_target_without_tracked_id():
    element = ScreenElement(
        kind="button",
        label="NOWA OFERTA",
        x=20,
        y=30,
        width=110,
        height=110,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "some_other_provider",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": "1-2-3",
        },
    )

    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(),
    )

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Click NOWA OFERTA",
            target="NOWA OFERTA",
        ),
        make_context(elements=(element,)),
    )

    assert result.success is False
    assert result.requires_manual_review is True
    assert "not a guarded UIA target" in result.message


def test_robot_action_executor_live_uia_path_rejects_missing_window_handle():
    mouse = RecordingMouse()
    robot = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        mouse=mouse,
    )

    result = robot.execute_uia_screen_element(
        screen_element=make_uia_element(),
        action=InteractionAction.CLICK,
        screen_origin=(100, 200),
        window_handle=None,
    )

    assert result.success is False
    assert result.executed is False
    assert "UIA safety gate rejected action" in result.reason
    assert mouse.points == []


def test_robot_action_executor_uia_path_rejects_disabled_target():
    mouse = RecordingMouse()
    robot = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        mouse=mouse,
    )

    result = robot.execute_uia_screen_element(
        screen_element=make_uia_element(enabled=False),
        action=InteractionAction.CLICK,
        screen_origin=(100, 200),
        window_handle=1234,
    )

    assert result.success is False
    assert result.executed is False
    assert "UIA safety gate rejected action" in result.reason
    assert mouse.points == []


def test_robot_action_executor_live_uia_path_requires_known_origin():
    mouse = RecordingMouse()
    robot = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=AllowingUIASafetyGate(),
        mouse=mouse,
    )

    result = robot.execute_uia_screen_element(
        screen_element=make_uia_element(),
        action=InteractionAction.CLICK,
        screen_origin=None,
        window_handle=1234,
    )

    assert result.success is False
    assert result.executed is False
    assert "requires a known screen origin" in result.reason
    assert mouse.points == []


def test_robot_gui_executor_targets_duplicate_labels_by_exact_uia_runtime_id():
    mouse = RecordingMouse()
    robot = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        mouse=mouse,
    )
    executor = RobotGUIExecutor(robot_action_executor=robot)

    first = make_uia_element(
        runtime_id="first-control",
        automation_id="IDC_WIDTH",
        x=20,
        y=30,
    )
    second = make_uia_element(
        runtime_id="second-control",
        automation_id="IDC_SASH_WIDTH",
        x=80,
        y=40,
    )
    query = SemanticTargetQuery(
        role="button",
        label="NOWA OFERTA",
        automation_id="IDC_SASH_WIDTH",
        uia_runtime_id="second-control",
        description="WindowHub sash width control",
    )

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Click the uniquely bound UIA control",
            target=query,
        ),
        make_context(elements=(first, second)),
    )

    assert result.success is True
    assert result.metadata["target_id"] == "uia:second-control"
    assert result.metadata["point"] == (235, 295)
    assert mouse.points == [(235, 295)]


def test_robot_gui_executor_fails_closed_for_duplicate_uia_runtime_identity():
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    first = make_uia_element(
        runtime_id="same-runtime",
        automation_id="IDC_WIDTH",
    )
    second = make_uia_element(
        runtime_id="same-runtime",
        automation_id="IDC_HEIGHT",
    )
    query = SemanticTargetQuery(
        role="button",
        label="NOWA OFERTA",
        uia_runtime_id="same-runtime",
        description="Duplicate UIA runtime identity",
    )

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Click an ambiguous UIA target",
            target=query,
        ),
        make_context(elements=(first, second)),
    )

    assert result.success is False
    assert mouse.points == []


def test_robot_gui_executor_rejects_duplicate_uia_identity_even_for_unique_label():
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    unique_label = make_uia_element(
        label="Customer reference",
        runtime_id="duplicate-runtime",
        automation_id="IDC_REFERENCE",
    )
    unrelated = make_uia_element(
        label="Different label",
        runtime_id="duplicate-runtime",
        automation_id="IDC_OTHER",
    )

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Click Customer reference",
            target="Customer reference",
        ),
        make_context(elements=(unique_label, unrelated)),
    )

    assert result.success is False
    assert result.requires_manual_review is True
    assert mouse.points == []
