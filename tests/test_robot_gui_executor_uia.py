from types import SimpleNamespace

import pytest

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


def make_quantity_element(*, runtime_id="quantity-runtime", label="Ile sztuk", automation_id="1001"):
    return ScreenElement(
        kind="edit",
        label=label,
        x=40,
        y=50,
        width=120,
        height=28,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "provider_element_id": f"uia:{runtime_id}",
            "automation_id": automation_id,
            "uia_control_type": "edit",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": runtime_id,
            "interaction_capability_confidence": 0.99,
        },
    )


def make_windowhub_form_context(elements, *, application="Okna.exe", title="Dodawanie nowej pozycji"):
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application=application,
            active_window_title=title,
        ),
        metadata={
            "window_handle": 1234,
            "window_rect": SimpleNamespace(left=100, top=200, width=1200, height=800),
        },
    )
    scene = ScreenScene(observation=observation, elements=tuple(elements))
    return ExecutionContext(
        request=AgentRequest(message="Set WindowHub quantity"),
        last_observation=observation,
        current_scene=scene,
    )


def _quantity_scope(runtime_id="quantity-runtime"):
    return {
        "field_name": "quantity_input",
        "application": "Okna.exe",
        "window_title": "Dodawanie nowej pozycji",
        "label": "Ile sztuk",
        "control_type": "edit",
        "automation_id": "1001",
        "uia_runtime_id": runtime_id,
    }


def test_windowhub_form_scope_rejects_when_foreground_application_changes():
    element = make_quantity_element()
    context = make_windowhub_form_context(
        (element,),
        application="Code.exe",
        title="source.py",
    )
    context.set_value("_windowhub_form_action_scope", _quantity_scope())
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    action = AgentAction(
        name="write_text",
        description="Set quantity",
        target=SemanticTargetQuery(
            role="edit",
            label="Ile sztuk",
            automation_id="1001",
            uia_runtime_id="quantity-runtime",
            description="WindowHub quantity field",
        ),
        value="2",
    )

    result = executor.execute(action, context)

    assert result.success is False
    assert result.requires_manual_review is True
    assert result.metadata["executed"] is False
    assert "Fresh observation" in result.message
    assert mouse.points == []


def test_windowhub_form_scope_rejects_reused_automation_id_for_description_field():
    description = make_quantity_element(
        runtime_id="description-runtime",
        label="Opis pozycji",
        automation_id="1001",
    )
    context = make_windowhub_form_context((description,))
    context.set_value("_windowhub_form_action_scope", _quantity_scope("quantity-runtime"))
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    action = AgentAction(
        name="write_text",
        description="Set quantity",
        target=SemanticTargetQuery(
            role="edit",
            label="Ile sztuk",
            automation_id="1001",
            uia_runtime_id="quantity-runtime",
            description="WindowHub quantity field",
        ),
        value="2",
    )

    result = executor.execute(action, context)

    assert result.success is False
    assert result.requires_manual_review is True
    assert result.metadata["executed"] is False
    assert mouse.points == []


def test_windowhub_form_scope_allows_only_exact_fresh_quantity_control():
    quantity = make_quantity_element()
    context = make_windowhub_form_context((quantity,))
    context.set_value("_windowhub_form_action_scope", _quantity_scope())
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    action = AgentAction(
        name="write_text",
        description="Set quantity",
        target=SemanticTargetQuery(
            role="edit",
            label="Ile sztuk",
            automation_id="1001",
            uia_runtime_id="quantity-runtime",
            description="WindowHub quantity field",
        ),
        value="2",
    )

    result = executor.execute(action, context)

    assert result.success is True
    assert result.metadata["execution_path"] == "uia_only"
    assert mouse.points == [(200, 264)]


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


def test_robot_gui_executor_checks_uia_identity_even_with_visual_tracking():
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    first = make_uia_element(
        label="Customer reference",
        runtime_id="duplicate-runtime",
        automation_id="IDC_REFERENCE",
    )
    first = ScreenElement(
        kind=first.kind,
        label=first.label,
        x=first.x,
        y=first.y,
        width=first.width,
        height=first.height,
        confidence=first.confidence,
        interaction_capability=first.interaction_capability,
        metadata={**dict(first.metadata), "tracked_object_id": "tracked-1"},
    )
    second = make_uia_element(
        label="Delivery address",
        runtime_id="duplicate-runtime",
        automation_id="IDC_ADDRESS",
    )
    second = ScreenElement(
        kind=second.kind,
        label=second.label,
        x=second.x,
        y=second.y,
        width=second.width,
        height=second.height,
        confidence=second.confidence,
        interaction_capability=second.interaction_capability,
        metadata={**dict(second.metadata), "tracked_object_id": "tracked-2"},
    )

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Click Customer reference",
            target="Customer reference",
        ),
        make_context(elements=(first, second)),
    )

    assert result.success is False
    assert result.requires_manual_review is True
    assert result.metadata["executed"] is False
    assert mouse.points == []


def _navigation_scope():
    return {
        "field_name": "wizard_next_dimensions",
        "application": "Okna.exe",
        "window_title": "Dodawanie nowej pozycji",
        "label": "Dalej >",
        "control_type": "button",
        "automation_id": "12324",
        "uia_runtime_id": "next-runtime",
        "required_quantity": "2",
    }


def _navigation_elements(*, quantity="2", selected=True, button_label="Dalej >"):
    qty = make_quantity_element()
    qty = ScreenElement(
        kind=qty.kind,
        label=qty.label,
        x=qty.x,
        y=qty.y,
        width=qty.width,
        height=qty.height,
        confidence=qty.confidence,
        interaction_capability=qty.interaction_capability,
        metadata={**dict(qty.metadata), "current_value": quantity},
    )
    window = ScreenElement(
        kind="radiobutton",
        label="Okno",
        x=50,
        y=100,
        width=70,
        height=30,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_runtime_id": "window-runtime",
            "automation_id": "1329",
            "uia_control_type": "radiobutton",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_selected": selected,
        },
    )
    button = ScreenElement(
        kind="button",
        label=button_label,
        x=150,
        y=100,
        width=90,
        height=35,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "provider_element_id": "uia:next-runtime",
            "uia_runtime_id": "next-runtime",
            "automation_id": "12324",
            "uia_control_type": "button",
            "uia_enabled": True,
            "uia_visible": True,
            "interaction_capability_confidence": 0.99,
        },
    )
    return (qty, window, button)


def _next_action():
    return AgentAction(
        name="click_screen_element",
        description="Move to dimensions",
        target=SemanticTargetQuery(
            role="button",
            label="Dalej >",
            automation_id="12324",
            uia_runtime_id="next-runtime",
            description="WindowHub Next button",
        ),
    )


def _execute_guarded_next(*, quantity="2", selected=True, button_label="Dalej >", application="Okna.exe"):
    context = make_windowhub_form_context(
        _navigation_elements(
            quantity=quantity, selected=selected, button_label=button_label
        ),
        application=application,
        title="Dodawanie nowej pozycji",
    )
    context.set_value("_windowhub_form_action_scope", _navigation_scope())
    mouse = RecordingMouse()
    executor = RobotGUIExecutor(
        robot_action_executor=RobotActionExecutor(
            mode=RobotExecutionMode.DRY_RUN,
            mouse=mouse,
        ),
    )
    return executor.execute(_next_action(), context), mouse


def test_navigation_guard_allows_fresh_matching_quantity_and_window_selection():
    result, mouse = _execute_guarded_next()
    assert result.success is True
    assert result.metadata["execution_path"] == "uia_only"
    assert mouse.points == [(295, 317)]


@pytest.mark.parametrize(
    "override",
    [
        {"quantity": "3"},
        {"quantity": None},
        {"selected": False},
        {"selected": None},
        {"button_label": "Anuluj"},
        {"application": "Code.exe"},
    ],
)
def test_navigation_guard_rejects_changed_state_before_any_mouse_action(override):
    result, mouse = _execute_guarded_next(**override)
    assert result.success is False
    assert result.requires_manual_review is True
    assert result.metadata["executed"] is False
    assert mouse.points == []
