"""Contract tests for live WindowHub overall-dimension writes."""
from types import SimpleNamespace

import pytest

from app.agent.agent_action import AgentAction
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
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
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def scene(*elements, title="Wielkość okna"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe", active_window_title=title,
            )
        ),
        elements=tuple(elements),
    )


def element(field, value="1000", runtime_id="runtime"):
    spec = WindowHubOfferFormMap().spec_for_field(field)
    return ScreenElement(
        kind="edit", label=spec.label, x=10, y=20, width=100, height=20,
        metadata={
            "source": "windows_ui_automation",
            "automation_id": spec.automation_id,
            "uia_control_type": "edit",
            "uia_runtime_id": runtime_id,
            "uia_enabled": True,
            "uia_visible": True,
            "current_value": value,
        },
    )


def entry(name, value):
    return WindowHubPlannedField(
        field_name=name, desired_value=value, source="test",
        handling=WindowHubPlanHandling.DIRECT_VALUE,
    )


@pytest.mark.parametrize(("field", "value"), [("width_1", 1230), ("height_1", 1478)])
def test_overall_dimensions_prepare_verified_write(field, value):
    e = element(field)
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        scene(e), entry(field, value)
    )
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action.name == "write_text"
    assert prepared.action.value == str(value)
    assert prepared.expected_outcome.expected_element_current_value == str(value)

    class FakeLoop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return "done"

    loop = FakeLoop()
    result = WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, scene(e), loop, request_message="Set overall window dimension"
    )
    assert result == "done"
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["window_title"] == "Wielkość okna"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene(e), scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene(e, title="Dodawanie nowej pozycji"), scope
    ) is False


@pytest.mark.parametrize("invalid", [0, -1, 99, 5001, True, "1230", None])
def test_invalid_dimensions_never_prepare_live_write(invalid):
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        scene(element("width_1")), entry("width_1", invalid)
    )
    assert prepared.status is WindowHubFormActionStatus.BLOCKED


def test_skos_controls_are_not_live_authorized():
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        scene(element("width_2")), entry("width_2", 120)
    )
    assert prepared.status is WindowHubFormActionStatus.BLOCKED
    assert prepared.action is None
