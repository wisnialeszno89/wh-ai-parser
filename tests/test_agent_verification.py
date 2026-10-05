from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)

from app.agent.verification.outcome_verifier import (
    OutcomeVerifier,
)


def create_scene(
    *,
    application="Notepad",
    title="Untitled - Notepad",
    elements=(),
):

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application=application,
            active_window_title=title,
            screen_width=1920,
            screen_height=1080,
        )
    )

    return ScreenScene(
        observation=observation,
        elements=elements,
    )


def test_verifier_accepts_matching_environment():

    verifier = OutcomeVerifier()

    scene = create_scene()

    expected = ExpectedOutcome(
        description="Notepad remains active.",
        expected_active_application="Notepad",
        expected_window_title="Untitled - Notepad",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is True


def test_verifier_rejects_wrong_application():

    verifier = OutcomeVerifier()

    scene = create_scene(
        application="Calculator"
    )

    expected = ExpectedOutcome(
        description="Notepad should be active.",
        expected_active_application="Notepad",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is False


def test_verifier_finds_expected_element():

    verifier = OutcomeVerifier()

    save_button = ScreenElement(
        kind="button",
        label="Save",
    )

    scene = create_scene(
        elements=(save_button,)
    )

    expected = ExpectedOutcome(
        description="Save button should exist.",
        expected_element_label="Save",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is True


def test_verifier_rejects_missing_element():

    verifier = OutcomeVerifier()

    scene = create_scene()

    expected = ExpectedOutcome(
        description="Save button should exist.",
        expected_element_label="Save",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is False


def test_verifier_accepts_disappeared_element():

    verifier = OutcomeVerifier()

    scene = create_scene()

    expected = ExpectedOutcome(
        description="Save dialog should disappear.",
        expected_element_label="Save changes?",
        element_should_exist=False,
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is True


def test_verifier_rejects_element_that_should_disappear():

    verifier = OutcomeVerifier()

    dialog = ScreenElement(
        kind="dialog",
        label="Save changes?",
    )

    scene = create_scene(
        elements=(dialog,)
    )

    expected = ExpectedOutcome(
        description="Save dialog should disappear.",
        expected_element_label="Save changes?",
        element_should_exist=False,
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is False


def test_verifier_finds_expected_element_kind():

    verifier = OutcomeVerifier()

    dialog = ScreenElement(
        kind="dialog",
        label="Save changes?",
    )

    scene = create_scene(
        elements=(dialog,)
    )

    expected = ExpectedOutcome(
        description="Dialog should be visible.",
        expected_element_kind="dialog",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is True


def test_verifier_rejects_missing_expected_element_kind():

    verifier = OutcomeVerifier()

    scene = create_scene()

    expected = ExpectedOutcome(
        description="Dialog should be visible.",
        expected_element_kind="dialog",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is False


def test_verifier_rejects_unchanged_scene_when_change_is_required():

    verifier = OutcomeVerifier()

    element = ScreenElement(
        kind="button",
        label="Open",
        x=10,
        y=20,
        width=30,
        height=40,
        metadata={
            "automation_id": "OpenButton",
            "uia_enabled": True,
            "uia_visible": True,
        },
    )

    scene = create_scene(
        elements=(element,)
    )

    expected = ExpectedOutcome(
        description="Click should change the scene.",
        require_scene_change=True,
        baseline_scene_signature=(
            (
                "Open",
                "button",
                10,
                20,
                30,
                40,
                "OpenButton",
                None,
                True,
                True,
            ),
        ),
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is False
    assert "did not change" in result.reason


def test_verifier_accepts_changed_scene_when_change_is_required():

    verifier = OutcomeVerifier()

    scene = create_scene(
        elements=(
            ScreenElement(
                kind="button",
                label="Next",
                x=10,
                y=20,
                width=30,
                height=40,
            ),
        )
    )

    expected = ExpectedOutcome(
        description="Click should change the scene.",
        require_scene_change=True,
        baseline_scene_signature=(
            (
                "Open",
                "button",
                10,
                20,
                30,
                40,
                None,
                None,
                None,
                None,
            ),
        ),
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is True


def test_verifier_accepts_expected_current_value():
    verifier = OutcomeVerifier()

    field = ScreenElement(
        kind="edit",
        label="Szerokość",
        metadata={
            "current_value": "1230",
        },
    )

    scene = create_scene(
        elements=(field,)
    )

    expected = ExpectedOutcome(
        description="Width should contain 1230.",
        expected_element_label="Szerokość",
        expected_element_current_value="1230",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is True


def test_verifier_rejects_unexpected_current_value():
    verifier = OutcomeVerifier()

    field = ScreenElement(
        kind="edit",
        label="Szerokość",
        metadata={
            "current_value": "1240",
        },
    )

    scene = create_scene(
        elements=(field,)
    )

    expected = ExpectedOutcome(
        description="Width should contain 1230.",
        expected_element_label="Szerokość",
        expected_element_current_value="1230",
    )

    result = verifier.verify(
        expected,
        scene,
    )

    assert result.verified is False
    assert result.metadata is not None
    assert result.metadata["actual_value"] == "1240"
