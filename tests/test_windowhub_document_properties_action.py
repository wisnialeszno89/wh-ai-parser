from types import SimpleNamespace
import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.offers.windowhub_document_properties_action import (
    DOCUMENT_PRICE_EXCLUSIONS, prepare_price_exclusion,
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
    return ScreenElement(
        kind="checkbox", label=label, x=20, y=30, width=100, height=20,
        metadata={
            "source": "windows_ui_automation",
            "automation_id": "A123",
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


def test_document_confirmation_requires_all_business_conditions():
    from app.agent.offers.windowhub_document_properties_action import (
        prepare_document_confirmation,
    )
    from app.agent.offers.windowhub_new_offer_mission import NewWindowOfferGoal
    from app.agent.offers.windowhub_position_mission import WindowPositionRequest

    goal = NewWindowOfferGoal(
        WindowPositionRequest(quantity=1, width_mm=1230, height_mm=1478)
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
        checkbox(label, checked=True, runtime_id="price-" + str(i))
        for i, label in enumerate(DOCUMENT_PRICE_EXCLUSIONS.values())
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
        checkbox("Bez ceny wykończenia", checked=False, runtime_id="price-3"),
        button,
    )
    assert RobotGUIExecutor._matches_windowhub_form_action_scope(
        prepared.action, unchecked_prices, scope
    ) is False
