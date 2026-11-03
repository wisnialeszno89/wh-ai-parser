from types import SimpleNamespace

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.expectation_resolver import ExpectationResolver
from app.agent.verification.outcome_verifier import OutcomeVerifier


def _scene(*, application="EXCEL.EXE", title="Workbook", focused=True):
    element = ScreenElement(
        kind="edit",
        label="Customer name",
        x=10,
        y=20,
        width=150,
        height=24,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "edit",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_focused": focused,
        },
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application=application,
                active_window_title=title,
            ),
            metadata={},
        ),
        elements=(element,),
    )


def test_keyboard_focus_is_a_verifiable_semantic_element_state():
    result = OutcomeVerifier().verify(
        ExpectedOutcome(
            description="The next field receives keyboard focus.",
            expected_element_label="Customer name",
            expected_element_state_name="uia_focused",
            expected_element_state_value=True,
        ),
        _scene(focused=True),
    )

    assert result.verified is True


def test_active_application_switch_changes_the_semantic_scene_signature():
    first = _scene(application="EXCEL.EXE", title="Workbook")
    second = _scene(application="chrome.exe", title="Browser")

    assert (
        ExpectationResolver._scene_signature(first)
        != ExpectationResolver._scene_signature(second)
    )

    result = OutcomeVerifier().verify(
        ExpectedOutcome(
            description="The active application changes.",
            require_scene_change=True,
            baseline_scene_signature=ExpectationResolver._scene_signature(first),
        ),
        second,
    )
    assert result.verified is True


def test_uia_focus_reader_uses_accessibility_focus_property():
    item = SimpleNamespace(
        element_info=SimpleNamespace(has_keyboard_focus=True),
    )

    assert WindowHubUIAutomationProvider._keyboard_focus_state(item) is True


def test_uia_focus_reader_returns_unknown_when_provider_has_no_focus_state():
    item = SimpleNamespace(element_info=SimpleNamespace())

    assert WindowHubUIAutomationProvider._keyboard_focus_state(item) is None
