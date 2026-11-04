from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.offers.windowhub_client_lookup_action import prepare_open_customer_lookup
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus, WindowHubOfferFormActionExecutor,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def scene(*elements, title="Właściwości dokumentu"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="Okna.exe", active_window_title=title)
        ),
        elements=tuple(elements),
    )


def lookup(*, runtime="customer-lookup", automation_id="IDC_ZAMAWIAJACY"):
    return ScreenElement(
        kind="button", label="LookUpEdit", x=10, y=20, width=80, height=20,
        metadata={
            "source": "windowhub_ui_automation",
            "uia_control_type": "button",
            "automation_id": automation_id,
            "uia_runtime_id": runtime,
            "uia_enabled": True, "uia_visible": True,
        },
    )


def test_customer_lookup_action_is_scoped_to_native_button():
    s = scene(lookup())
    prepared = prepare_open_customer_lookup(s)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action.target.automation_id == "IDC_ZAMAWIAJACY"

    class Loop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None

    loop = Loop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, s, loop, request_message="Open customer lookup"
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["window_title"] == "Właściwości dokumentu"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, s, scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene(lookup(), title="Wielkość okna"), scope
    ) is False


def test_lookup_blocks_ambiguous_and_unverified_controls():
    assert prepare_open_customer_lookup(scene()).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_open_customer_lookup(
        scene(lookup(), lookup(runtime="another"))
    ).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_open_customer_lookup(
        scene(lookup(automation_id="IDC_KONTAKT"))
    ).status is WindowHubFormActionStatus.BLOCKED
