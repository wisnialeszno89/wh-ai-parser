from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.offers.windowhub_customer_creation_action import (
    prepare_add_customer, prepare_customer_name, prepare_confirm_new_customer,
)
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubOfferFormActionExecutor, WindowHubFormActionStatus,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def scene(title, *elements):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="Okna.exe", active_window_title=title)
        ), elements=tuple(elements),
    )


def control(kind, label, *, value=None, rid=None):
    return ScreenElement(
        kind=kind, label=label, x=20, y=20, width=110, height=25,
        metadata={
            "source": "windows_ui_automation", "uia_control_type": kind,
            "uia_runtime_id": rid or kind + "-" + label,
            "automation_id": None, "current_value": value,
            "uia_visible": True, "uia_enabled": True,
        },
    )


def test_add_requires_unique_button():
    title = "Właściwości dokumentu"
    assert prepare_add_customer(scene(title, control("button", "Dodaj"))).status is WindowHubFormActionStatus.READY
    assert prepare_add_customer(scene(title)).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_add_customer(scene(title, control("button", "Dodaj"), control("button", "Dodaj", rid="other"))).status is WindowHubFormActionStatus.BLOCKED


def test_name_write_and_ok_guard():
    title = "Zakładanie nowego klienta"
    prepared = prepare_customer_name(scene(title, control("edit", "Firma", value="")), "XYZ TEST AGENT")
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action.value == "XYZ TEST AGENT"
    observed = scene(title, control("edit", "Firma", value="XYZ TEST AGENT"), control("button", "OK"))
    confirmed = prepare_confirm_new_customer(observed, "XYZ TEST AGENT")
    assert confirmed.required_customer_name == "XYZ TEST AGENT"

    class Loop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None

    loop = Loop()
    WindowHubOfferFormActionExecutor.execute_prepared(confirmed, observed, loop, request_message="Confirm customer")
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["required_customer_name"] == "XYZ TEST AGENT"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(confirmed.action, observed, scope)
    changed = scene(title, control("edit", "Firma", value="WRONG"), control("button", "OK"))
    assert not RobotGUIExecutor._matches_windowhub_form_action_scope(confirmed.action, changed, scope)


def test_wrong_name_cannot_be_confirmed():
    title = "Zakładanie nowego klienta"
    assert prepare_confirm_new_customer(scene(title, control("edit", "Firma", value="")), "XYZ").status is WindowHubFormActionStatus.BLOCKED
