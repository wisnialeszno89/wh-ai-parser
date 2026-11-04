"""Fail-closed contract tests for the first supervised WindowHub Next click."""
from types import SimpleNamespace

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus,
    WindowHubOfferFormActionExecutor,
)
from app.agent.offers.windowhub_wizard_navigation import WindowHubPositionToDimensionsPlanner
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def element(role, label, automation_id, runtime_id, *, value=None, selected=None, enabled=True):
    meta = {
        "source": "windows_ui_automation",
        "uia_runtime_id": runtime_id,
        "uia_control_type": role,
        "automation_id": automation_id,
        "uia_enabled": enabled,
        "uia_visible": True,
        "current_value": value,
    }
    if selected is not None:
        meta["uia_selected"] = selected
    return ScreenElement(
        kind=role,
        label=label,
        x=10,
        y=20,
        width=120,
        height=28,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata=meta,
    )


def scene(*elements, title="Dodawanie nowej pozycji", application="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=application,
                active_window_title=title,
            )
        ),
        elements=tuple(elements),
    )


def valid_scene(*extra, quantity="2", selected=True, next_label="Dalej >", next_id="12324"):
    return scene(
        element("edit", "Ile sztuk", "1001", "qty-runtime", value=quantity),
        element("radiobutton", "Okno", "1329", "window-runtime", selected=selected),
        element("button", next_label, next_id, "next-runtime"),
        *extra,
    )


def test_prepares_only_next_click_with_exact_step_title_expectation():
    prepared = WindowHubPositionToDimensionsPlanner().prepare(valid_scene(), expected_quantity=2)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action.name == "click_screen_element"
    assert prepared.action.target.role == "button"
    assert prepared.action.target.label == "Dalej >"
    assert prepared.action.target.automation_id == "12324"
    assert prepared.action.target.uia_runtime_id == "next-runtime"
    assert prepared.action.requires_environment_observation is True
    assert prepared.required_quantity == "2"
    assert prepared.expected_outcome.expected_active_application == "Okna.exe"
    assert prepared.expected_outcome.expected_window_title == "Wielkość okna"


@pytest.mark.parametrize(
    "prepared_scene",
    [
        valid_scene(quantity="1"),
        valid_scene(selected=False),
        valid_scene(selected=None),
        valid_scene(next_label="Anuluj"),
        valid_scene(next_id="2"),
        valid_scene(element("button", "Dalej >", "12324", "second-next")),
        valid_scene(element("button", "Other", "777", "next-runtime")),
        scene(title="Parametry szklenia"),
        scene(application="Code.exe"),
    ],
)
def test_unsafe_navigation_is_blocked(prepared_scene):
    prepared = WindowHubPositionToDimensionsPlanner().prepare(
        prepared_scene, expected_quantity=2
    )
    assert prepared.status is WindowHubFormActionStatus.BLOCKED
    assert prepared.action is None


@pytest.mark.parametrize("quantity", (0, -1, True, "2", None))
def test_invalid_expected_quantity_blocks_navigation(quantity):
    prepared = WindowHubPositionToDimensionsPlanner().prepare(
        valid_scene(), expected_quantity=quantity
    )
    assert prepared.status is WindowHubFormActionStatus.BLOCKED


def test_dimensions_already_active_never_clicks():
    prepared = WindowHubPositionToDimensionsPlanner().prepare(
        scene(title="Wielkość okna"), expected_quantity=2
    )
    assert prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED
    assert prepared.action is None


def test_one_step_executor_carries_exact_quantity_into_fresh_scope():
    current_scene = valid_scene()
    prepared = WindowHubPositionToDimensionsPlanner().prepare(
        current_scene, expected_quantity=2
    )

    class FakeLoop:
        context = None
        plan = None

        def run(self, *, plan, context):
            self.plan = plan
            self.context = context
            return SimpleNamespace(success=True)

    control_loop = FakeLoop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared,
        current_scene,
        control_loop,
        request_message="Next one step only",
    )
    assert len(control_loop.plan.steps) == 1
    assert control_loop.plan.steps[0].action.name == "click_screen_element"
    assert control_loop.context.get_value("_windowhub_form_action_scope")["required_quantity"] == "2"
    expected = control_loop.context.get_value("expected_outcomes")["click_screen_element"]
    assert expected.expected_window_title == "Wielkość okna"
