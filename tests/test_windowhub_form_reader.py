from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_form_reader import (
    WindowHubFormReader,
)


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
        },
    )


def field(label, value, scope=None, kind="edit"):
    metadata = {
        "current_value": value,
        "source": "windowhub_ui_automation",
    }
    if scope is not None:
        metadata["document_scope"] = scope

    return ScreenElement(
        kind=kind,
        label=label,
        confidence=0.99,
        metadata=metadata,
    )


def test_reader_extracts_observed_field_values():
    scene = make_scene(
        field("Szerokość", "1230", "OFR/4024"),
        field("Wysokość", "1480", "OFR/4024"),
        field("Kolor", "Biały", "OFR/4024", kind="combobox"),
    )

    fields = WindowHubFormReader().read_active_document(scene)

    assert [(item.label, item.value) for item in fields] == [
        ("Szerokość", "1230"),
        ("Wysokość", "1480"),
        ("Kolor", "Biały"),
    ]
    assert all(item.scope_status == "active_document" for item in fields)


def test_reader_does_not_mix_fields_from_other_document():
    scene = make_scene(
        field("Szerokość", "1230", "OFR/4024"),
        field("Szerokość", "900", "OFR/4025"),
    )

    fields = WindowHubFormReader().read_active_document(scene)

    assert len(fields) == 1
    assert fields[0].value == "1230"
    assert fields[0].document_scope == "OFR/4024"


def test_reader_marks_unscoped_field_as_unknown():
    scene = make_scene(
        field("Szerokość", "1230"),
    )

    fields = WindowHubFormReader().read(scene)

    assert len(fields) == 1
    assert fields[0].scope_status == "unknown"

    assert WindowHubFormReader().read_active_document(scene) == ()


def test_reader_returns_nothing_for_unresolved_active_document():
    scene = make_scene(
        field("Szerokość", "1230", "OFR/4024"),
        field("Wysokość", "1480", "OFR/4025"),
        active_document=None,
    )

    assert WindowHubFormReader().read_active_document(scene) == ()


def test_reader_ignores_non_form_controls():
    scene = make_scene(
        field("Szerokość", "1230", "OFR/4024"),
        ScreenElement(
            kind="button",
            label="Zapisz",
            metadata={
                "current_value": "",
                "document_scope": "OFR/4024",
            },
        ),
    )

    fields = WindowHubFormReader().read_active_document(scene)

    assert len(fields) == 1
    assert fields[0].label == "Szerokość"
