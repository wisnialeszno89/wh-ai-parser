from types import SimpleNamespace

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus,
    WindowHubOfferFormActionExecutor,
    WindowHubOfferFormActionPlanner,
)
from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
from app.agent.offers.windowhub_offer_form_plan import (
    WindowHubPlannedField,
    WindowHubPlanHandling,
)
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _scene(*elements, title="Dodawanie nowej pozycji"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title=title,
            ),
        ),
        elements=tuple(elements),
    )


def _element(
    field_name,
    *,
    runtime_id="runtime-1",
    current_value=None,
    selected=None,
    focused=False,
    enabled=True,
    visible=True,
    source="windows_ui_automation",
):
    spec = WindowHubOfferFormMap().spec_for_field(field_name)
    metadata = {
        "source": source,
        "automation_id": spec.automation_id,
        "uia_control_type": spec.control_type,
        "uia_runtime_id": runtime_id,
        "uia_enabled": enabled,
        "uia_visible": visible,
        "uia_focused": focused,
        "interaction_capability_confidence": 0.99,
        "current_value": current_value,
    }
    if isinstance(selected, bool):
        metadata["uia_selected"] = selected
    return ScreenElement(
        kind=spec.control_type,
        label=spec.label,
        x=10,
        y=20,
        width=120,
        height=28,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata=metadata,
    )


def _entry(field_name, desired_value, handling):
    return WindowHubPlannedField(
        field_name=field_name,
        desired_value=desired_value,
        source="test",
        handling=handling,
    )


def test_quantity_field_prepares_one_exact_write_with_value_postcondition():
    element = _element("quantity_input", runtime_id="quantity-runtime")
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element),
        _entry("quantity_input", 3, WindowHubPlanHandling.DIRECT_VALUE),
    )

    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action is not None
    assert prepared.action.name == "write_text"
    assert prepared.action.value == "3"
    assert prepared.action.target.uia_runtime_id == "quantity-runtime"
    assert prepared.expected_outcome is not None
    assert prepared.expected_outcome.expected_element_current_value == "3"
    assert prepared.expected_outcome.expected_element_uia_runtime_id == "quantity-runtime"


def test_already_selected_window_item_is_a_noop_not_a_click():
    element = _element("item_type_window", runtime_id="window-runtime", selected=True)
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element),
        _entry("item_type_window", True, WindowHubPlanHandling.RADIO_SELECTION),
    )

    assert prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED
    assert prepared.action is None
    assert prepared.expected_outcome is None


def test_unselected_window_item_prepares_click_with_selected_state_postcondition():
    element = _element("item_type_window", runtime_id="window-runtime", selected=False)
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element),
        _entry("item_type_window", True, WindowHubPlanHandling.RADIO_SELECTION),
    )

    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action is not None
    assert prepared.action.name == "click_screen_element"
    assert prepared.expected_outcome is not None
    assert prepared.expected_outcome.expected_element_state_name == "uia_selected"
    assert prepared.expected_outcome.expected_element_state_value is True


def test_unknown_radio_selection_blocks_click_even_when_control_is_focused():
    element = _element(
        "item_type_window",
        runtime_id="window-runtime",
        focused=True,
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element),
        _entry("item_type_window", True, WindowHubPlanHandling.RADIO_SELECTION),
    )

    assert prepared.status is WindowHubFormActionStatus.BLOCKED
    assert prepared.action is None
    assert "unknown" in prepared.reason


def test_duplicate_runtime_id_blocks_quantity_write():
    target = _element("quantity_input", runtime_id="duplicate-runtime")
    other = ScreenElement(
        kind="edit",
        label="Other",
        x=150,
        y=20,
        width=120,
        height=28,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_runtime_id": "duplicate-runtime",
            "uia_enabled": True,
            "uia_visible": True,
        },
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(target, other),
        _entry("quantity_input", 2, WindowHubPlanHandling.DIRECT_VALUE),
    )

    assert prepared.status is WindowHubFormActionStatus.BLOCKED
    assert prepared.action is None
    assert "not unique" in prepared.reason


@pytest.mark.parametrize("quantity", (0, -1, True, "2", None))
def test_invalid_quantity_never_prepares_write(quantity):
    element = _element("quantity_input", runtime_id="quantity-runtime")
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element),
        _entry("quantity_input", quantity, WindowHubPlanHandling.DIRECT_VALUE),
    )

    assert prepared.status is WindowHubFormActionStatus.BLOCKED
    assert prepared.action is None


def test_quantity_already_present_is_noop():
    element = _element(
        "quantity_input",
        runtime_id="quantity-runtime",
        current_value="4",
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element),
        _entry("quantity_input", 4, WindowHubPlanHandling.DIRECT_VALUE),
    )

    assert prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED
    assert prepared.action is None


def test_later_catalog_field_is_not_live_executable():
    element = _element(
        "glazing_package",
        runtime_id="glazing-runtime",
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(element, title="Parametry szklenia"),
        _entry("glazing_package", "3glass", WindowHubPlanHandling.CATALOG_SELECTION),
    )

    assert prepared.status is WindowHubFormActionStatus.BLOCKED
    assert prepared.action is None


def test_executor_delegates_exactly_one_action_and_expected_outcome():
    element = _element("quantity_input", runtime_id="quantity-runtime")
    scene = _scene(element)
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        scene,
        _entry("quantity_input", 2, WindowHubPlanHandling.DIRECT_VALUE),
    )

    class FakeControlLoop:
        def __init__(self):
            self.plan = None
            self.context = None

        def run(self, *, plan, context):
            self.plan = plan
            self.context = context
            return "control-loop-result"

    control_loop = FakeControlLoop()
    result = WindowHubOfferFormActionExecutor.execute_prepared(
        prepared,
        scene,
        control_loop,
        request_message="Set the quantity to 2.",
        session_id="test-session",
    )

    assert result == "control-loop-result"
    assert len(control_loop.plan.steps) == 1
    assert control_loop.plan.steps[0].action.name == "write_text"
    expected = control_loop.context.get_value("expected_outcomes")
    assert expected["write_text"].expected_element_current_value == "2"
    assert control_loop.context.current_scene is scene


def test_executor_refuses_to_run_unprepared_action():
    scene = _scene(_element("quantity_input"))
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        scene,
        _entry("quantity_input", 1, WindowHubPlanHandling.DIRECT_VALUE),
    )
    blocked = WindowHubOfferFormActionPlanner().prepare_entry(
        _scene(_element("quantity_input", runtime_id=None)),
        _entry("quantity_input", 1, WindowHubPlanHandling.DIRECT_VALUE),
    )

    class FakeControlLoop:
        def run(self, **kwargs):
            raise AssertionError("control loop must not run for a blocked action")

    with pytest.raises(ValueError, match="windowhub_form_action_not_ready"):
        WindowHubOfferFormActionExecutor.execute_prepared(
            blocked,
            scene,
            FakeControlLoop(),
            request_message="Must not run.",
        )
