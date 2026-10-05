from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.target_resolver import TargetResolver


def make_scene(*elements, active_document="OFR/4024"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_window_title="Okna - WindowHub",
            ),
        ),
        elements=tuple(elements),
        metadata={
            "active_document": active_document,
            "active_document_resolution": (
                "resolved" if active_document else "unresolved"
            ),
        },
    )


def field(label, document_scope):
    return ScreenElement(
        kind="edit",
        label=label,
        metadata={
            "document_scope": document_scope,
            "source": "windowhub_ui_automation",
        },
    )


def test_resolver_prefers_matching_active_document_scope():
    active = field("Szerokość", "OFR/4024")
    inactive = field("Szerokość", "OFR/4025")

    result = TargetResolver().resolve(
        make_scene(active, inactive),
        "Szerokość",
    )

    assert result.resolved is True
    assert result.element is active
    assert "Active document scope" in result.reason


def test_resolver_rejects_duplicate_target_without_explicit_scope():
    active = ScreenElement(
        kind="edit",
        label="Szerokość",
        metadata={"source": "windowhub_ui_automation"},
    )
    inactive = field("Szerokość", "OFR/4025")

    result = TargetResolver().resolve(
        make_scene(active, inactive),
        "Szerokość",
    )

    assert result.resolved is False
    assert result.element is None
    assert "outside active document" in result.reason


def test_resolver_does_not_guess_when_active_document_is_unresolved():
    first = field("Szerokość", "OFR/4024")
    second = field("Szerokość", "OFR/4025")

    scene = make_scene(
        first,
        second,
        active_document=None,
    )
    scene.metadata["active_document_resolution"] = "unresolved"

    result = TargetResolver().resolve(
        scene,
        "Szerokość",
    )

    assert result.resolved is False
    assert result.element is None
    assert "active document is not reliably resolved" in result.reason


def test_resolver_keeps_unique_non_scoped_target_backward_compatible():
    button = ScreenElement(
        kind="button",
        label="NOWA OFERTA",
        metadata={"source": "windowhub_ui_automation"},
    )

    result = TargetResolver().resolve(
        make_scene(button),
        "NOWA OFERTA",
    )

    assert result.resolved is True
    assert result.element is button
