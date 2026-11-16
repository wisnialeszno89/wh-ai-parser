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


def test_workspace_new_offer_allowed_from_existing_offer():
    from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_workspace
    prepared = prepare_new_offer_from_workspace(
        _scene(_tile(), title="Okna - OFR/4669-")
    )
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.expected_outcome.expected_window_title == "Właściwości dokumentu"


def test_legacy_start_action_stays_start_only():
    assert prepare_new_offer_from_start(
        _scene(_tile(), title="Okna - OFR/4669-")
    ).status is WindowHubFormActionStatus.BLOCKED


def test_workspace_new_offer_rejects_ambiguous_or_wrong_stage():
    from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_workspace
    assert prepare_new_offer_from_workspace(
        _scene(_tile(), _tile(runtime="other"), title="Okna - OFR/4669-")
    ).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_new_offer_from_workspace(
        _scene(_tile(), title="Wielkość okna")
    ).status is WindowHubFormActionStatus.BLOCKED


def test_existing_offer_execution_scope_uses_actual_document_title():
    from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_workspace
    prepared = prepare_new_offer_from_workspace(
        _scene(_tile(), title="Okna - OFR/4670-")
    )
    class Loop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None
    loop = Loop()
    source = _scene(_tile(), title="Okna - OFR/4670-")
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, source, loop, request_message="Open a separate new unsaved offer"
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["window_title"] == "Okna - OFR/4670-"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, source, scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, _scene(_tile(), title="Okna - OFR/OTHER"), scope
    ) is False
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, _scene(_tile(), title="Właściwości dokumentu"), scope
    ) is False




def _tab(runtime="start1-tab", *, selected=False):
    original = _tile(runtime=runtime, role="tabitem", label="Start1")
    from dataclasses import replace
    return replace(original, metadata={
        **original.metadata,
        "uia_selected": selected,
    })


def test_start1_tab_can_be_prepared_from_offer_document():
    from app.agent.offers.windowhub_new_offer_action import prepare_start1_navigation_from_offer
    scene = _scene(_tab(runtime="tab-id"), title="Okna - OFR/4670-")
    prepared = prepare_start1_navigation_from_offer(scene)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.expected_outcome.expected_window_title == "Okna - Start1"

    class Loop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None

    loop = Loop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, scene, loop, request_message="Switch to Start1"
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["field_name"] == "navigate_start1"
    assert scope["window_title"] == "Okna - OFR/4670-"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene, scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action,
        _scene(_tab(runtime="tab-id"), title="Okna - OFR/9999-"),
        scope
    ) is False


def test_start1_tab_rejects_wrong_screen_and_duplicates():
    from app.agent.offers.windowhub_new_offer_action import prepare_start1_navigation_from_offer
    tab = _tab(runtime="tab-id")
    assert prepare_start1_navigation_from_offer(
        _scene(tab, title="Okna - Start1")
    ).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_start1_navigation_from_offer(
        _scene(tab, _tab(runtime="other"), title="Okna - OFR/4670-")
    ).status is WindowHubFormActionStatus.BLOCKED


def test_start1_requires_real_unselected_tabitem():
    from app.agent.offers.windowhub_new_offer_action import prepare_start1_navigation_from_offer
    scene_title = "Okna - OFR/4670-"
    assert prepare_start1_navigation_from_offer(
        _scene(_tile(runtime="wrong-role", role="button", label="Start1"), title=scene_title)
    ).status is WindowHubFormActionStatus.BLOCKED
    assert prepare_start1_navigation_from_offer(
        _scene(_tab(selected=True), title=scene_title)
    ).status is WindowHubFormActionStatus.BLOCKED
    from dataclasses import replace
    tab = _tab()
    assert prepare_start1_navigation_from_offer(
        _scene(replace(tab, metadata={**tab.metadata, "uia_selected": None}), title=scene_title)
    ).status is WindowHubFormActionStatus.BLOCKED
