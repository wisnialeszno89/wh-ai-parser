from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_start
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus, WindowHubOfferFormActionExecutor,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _scene(*elements, title="Okna - Start1"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="Okna.exe", active_window_title=title),
        ),
        elements=tuple(elements),
    )


def _tile(runtime="new-offer-id", *, role="button", label="NOWA OFERTA"):
    return ScreenElement(
        kind=role, label=label, x=10, y=20, width=100, height=100,
        metadata={
            "source": "windows_ui_automation",
            "uia_runtime_id": runtime,
            "automation_id": None,
            "uia_control_type": role,
            "uia_visible": True,
            "uia_enabled": True,
        },
    )


def test_start_action_requires_unique_semantic_button():
    assert prepare_new_offer_from_start(_scene()).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_new_offer_from_start(_scene(_tile(role="text"))).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_new_offer_from_start(
        _scene(_tile(), _tile(runtime="other"))
    ).status is WindowHubFormActionStatus.BLOCKED


def test_start_action_scope_is_checked_against_fresh_window():
    scene = _scene(_tile())
    prepared = prepare_new_offer_from_start(scene)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.expected_outcome.expected_window_title == "Właściwości dokumentu"

    class Loop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None

    loop = Loop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, scene, loop, request_message="Open one new offer"
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["window_title"] == "Okna - Start1"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene, scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, _scene(_tile(), title="Właściwości dokumentu"), scope
    ) is False


def test_start_action_rejects_wrong_environment():
    assert prepare_new_offer_from_start(
        _scene(_tile(), title="Wielkość okna")
    ).status is WindowHubFormActionStatus.BLOCKED
