from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.outcome_verifier import OutcomeVerifier


def _element(label, automation_id, runtime_id, current_value):
    return ScreenElement(
        kind="edit",
        label=label,
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "edit",
            "automation_id": automation_id,
            "uia_runtime_id": runtime_id,
            "current_value": current_value,
        },
    )


def _scene(elements):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title="Wielkość okna",
            )
        ),
        elements=tuple(elements),
    )


def test_outcome_verifier_checks_value_on_exact_uia_control_when_labels_repeat():
    first = _element("Szerokość", "1000", "[frame-width]", "1200")
    second = _element("Szerokość", "1014", "[sash-width]", "800")
    expected = ExpectedOutcome(
        description="The requested sash width was entered.",
        expected_element_label="Szerokość",
        expected_element_current_value="800",
        expected_element_uia_runtime_id="[sash-width]",
        expected_element_automation_id="1014",
    )

    result = OutcomeVerifier().verify(expected, _scene((first, second)))

    assert result.verified is True


def test_outcome_verifier_rejects_duplicate_uia_runtime_identity():
    first = _element("Szerokość", "1000", "[duplicate]", "1200")
    second = _element("Wysokość", "1001", "[duplicate]", "1500")
    expected = ExpectedOutcome(
        description="The exact field should contain the requested value.",
        expected_element_label="Szerokość",
        expected_element_current_value="1200",
        expected_element_uia_runtime_id="[duplicate]",
    )

    result = OutcomeVerifier().verify(expected, _scene((first, second)))

    assert result.verified is False
    assert "ambiguous" in result.reason.lower()


def test_outcome_verifier_does_not_fall_back_to_label_when_uia_identity_missing():
    element = _element("Szerokość", "1000", "[actual]", "1200")
    expected = ExpectedOutcome(
        description="A different exact target should be checked.",
        expected_element_label="Szerokość",
        expected_element_current_value="1200",
        expected_element_uia_runtime_id="[missing]",
        expected_element_automation_id="1000",
    )

    result = OutcomeVerifier().verify(expected, _scene((element,)))

    assert result.verified is False
    assert "missing or ambiguous" in result.reason.lower()
