from types import SimpleNamespace
import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.offers.windowhub_document_properties_action import (
    DOCUMENT_PRICE_EXCLUSIONS, DOCUMENT_PRICE_AUTOMATION_IDS, prepare_price_exclusion,
)
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus, WindowHubOfferFormActionExecutor,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def scene(*elements, title="Właściwości dokumentu"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe", active_window_title=title
            )
        ),
        elements=tuple(elements),
    )


def checkbox(label, *, checked=False, runtime_id="unique-1"):
    automation_id = {
        v: DOCUMENT_PRICE_AUTOMATION_IDS[k]
        for k, v in DOCUMENT_PRICE_EXCLUSIONS.items()
    }.get(label, "A123")
    return ScreenElement(
        kind="checkbox", label=label, x=20, y=30, width=100, height=20,
        metadata={
            "source": "windows_ui_automation",
            "automation_id": automation_id,
            "uia_runtime_id": runtime_id,
            "uia_control_type": "checkbox",
            "uia_visible": True,
            "uia_enabled": True,
            "uia_checked": checked,
        },
    )


@pytest.mark.parametrize("name", DOCUMENT_PRICE_EXCLUSIONS)
def test_price_toggle_verified_and_guarded(name):
    element = checkbox(DOCUMENT_PRICE_EXCLUSIONS[name])
    s = scene(element)
    prepared = prepare_price_exclusion(s, name)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.action.name == "click_screen_element"
    assert prepared.expected_outcome.expected_element_state_name == "uia_checked"
    assert prepared.expected_outcome.expected_element_state_value is True

    class FakeLoop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return SimpleNamespace(success=True)

    loop = FakeLoop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, s, loop, request_message="Enable one exclusion"
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["window_title"] == "Właściwości dokumentu"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, s, scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene(checkbox(DOCUMENT_PRICE_EXCLUSIONS[name], checked=True)), scope
    ) is False


@pytest.mark.parametrize("checked", [None, "unknown", 2])
def test_unknown_checkbox_state_fails_closed(checked):
    result = prepare_price_exclusion(
        scene(checkbox("Bez ceny konstrukcji", checked=checked)),
        "exclude_construction_price",
    )
    assert result.status is WindowHubFormActionStatus.BLOCKED


def test_already_checked_is_not_clicked():
    result = prepare_price_exclusion(
        scene(checkbox("Bez ceny konstrukcji", checked=True)),
        "exclude_construction_price",
    )
    assert result.status is WindowHubFormActionStatus.ALREADY_SATISFIED
    assert result.action is None


def test_duplicate_checkbox_identity_is_blocked():
    result = prepare_price_exclusion(
        scene(
            checkbox("Bez ceny montażu", runtime_id="same"),
            checkbox("Inne", runtime_id="same"),
        ),
        "exclude_installation_price",
    )
    assert result.status is WindowHubFormActionStatus.BLOCKED


def test_price_action_wrong_dialog_is_blocked():
    result = prepare_price_exclusion(
        scene(checkbox("Bez ceny konstrukcji"), title="Wielkość okna"),
        "exclude_construction_price",
    )
    assert result.status is WindowHubFormActionStatus.BLOCKED


@pytest.mark.parametrize("excluded", [("construction", "installation", "removal", "finishing"), ("construction", "installation")])
def test_document_confirmation_requires_all_business_conditions(excluded):
    from app.agent.offers.windowhub_document_properties_action import (
        prepare_document_confirmation,
    )
    from app.agent.offers.windowhub_new_offer_mission import NewWindowOfferGoal
    from app.agent.offers.windowhub_position_mission import WindowPositionRequest

    goal = NewWindowOfferGoal(
        WindowPositionRequest(quantity=1, width_mm=1230, height_mm=1478),
        excluded_prices=excluded,
    )
    def client(value="TEST CUSTOMER"):
        return ScreenElement(
            kind="combobox", label="Klient",
            metadata={
                "source": "windows_ui_automation",
                "uia_enabled": True, "uia_visible": True,
                "current_value": value, "uia_runtime_id": "client-unique",
            },
        )
    button = ScreenElement(
        kind="button", label="OK",
        metadata={
            "source": "windows_ui_automation",
            "automation_id": "1",
            "uia_control_type": "button",
            "uia_runtime_id": "ok-unique",
            "uia_enabled": True, "uia_visible": True,
        },
    )
    checked_controls = tuple(
        checkbox(DOCUMENT_PRICE_EXCLUSIONS[key], checked=checked, runtime_id="price-" + str(i))
        for i, (key, checked) in enumerate(goal.price_states)
    )
    valid = scene(client(), *checked_controls, button)
    prepared = prepare_document_confirmation(valid, goal)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.expected_outcome.expected_active_application == "Okna.exe"

    class FakeLoop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None

    loop = FakeLoop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, valid, loop, request_message="Confirm validated document"
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, valid, scope
    ) is True
    wrong_client = scene(client(value=""), *checked_controls, button)
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, wrong_client, scope
    ) is False
    unchecked_prices = scene(
        client(), *checked_controls[:-1],
        checkbox("Bez ceny wykończenia", checked="finishing" not in excluded, runtime_id="price-3"),
        button,
    )
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, unchecked_prices, scope
    ) is False


def test_defer_route_clicks_cancel_only_with_explicit_policy():
    from app.agent.offers.windowhub_document_properties_action import (
        prepare_defer_document_properties,
    )
    from app.agent.offers.windowhub_new_offer_mission import NewWindowOfferGoal
    from app.agent.offers.windowhub_position_mission import WindowPositionRequest

    position = WindowPositionRequest(quantity=1, width_mm=1230, height_mm=1478)
    normal = NewWindowOfferGoal(position)
    deferred = NewWindowOfferGoal(position, customer_policy="defer_to_salesperson")
    cancel = ScreenElement(
        kind="button", label="Anuluj",
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "button",
            "automation_id": "2",
            "uia_runtime_id": "cancel-unique",
            "uia_enabled": True, "uia_visible": True,
        },
    )
    observed = scene(cancel)
    denied = prepare_defer_document_properties(observed, normal)
    assert denied.status is WindowHubFormActionStatus.BLOCKED
    prepared = prepare_defer_document_properties(observed, deferred)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.expected_outcome.expected_window_title == "Dodawanie nowej pozycji"

    class FakeLoop:
        context = None
        def run(self, *, plan, context):
            self.context = context
            return None

    loop = FakeLoop()
    WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, observed, loop,
        request_message="Defer document preferences explicitly",
    )
    scope = loop.context.get_value("_windowhub_form_action_scope")
    assert scope["window_title"] == "Właściwości dokumentu"
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, observed, scope
    ) is True
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, scene(cancel, title="Wielkość okna"), scope
    ) is False
    assert prepare_defer_document_properties(
        scene(cancel, cancel), deferred
    ).status is WindowHubFormActionStatus.BLOCKED

def test_checked_exclusion_is_cleared_only_if_still_checked():
    name = "exclude_installation_price"
    label = DOCUMENT_PRICE_EXCLUSIONS[name]
    before = scene(checkbox(label, checked=True))
    after = scene(checkbox(label, checked=False))
    prepared = prepare_price_exclusion(before, name, desired_checked=False)
    assert prepared.status is WindowHubFormActionStatus.READY
    assert prepared.expected_outcome.expected_element_state_value is False

    class FakeLoop:
        def run(self, *, plan, context):
            self.scope = context.get_value("_windowhub_form_action_scope")

    loop = FakeLoop()
    WindowHubOfferFormActionExecutor.execute_prepared(prepared, before, loop, request_message="Set order preference")
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(prepared.action, before, loop.scope)
    assert not RobotGUIExecutor._matches_windowhub_form_action_scope(prepared.action, after, loop.scope)
    assert prepare_price_exclusion(after, name, desired_checked=False).status is WindowHubFormActionStatus.ALREADY_SATISFIED
