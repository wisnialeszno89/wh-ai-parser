"""Verified semantic skill bindings for multiple MDI WindowHub offers."""
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene


def scene(*elements, title="Okna - OFR/4680-"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="Okna.exe", active_window_title=title),
        ),
        elements=tuple(elements),
    )


def button(runtime="one", *, label="Dodaj", scope=None, ancestors=()):
    return ScreenElement(
        kind="button", label=label, x=10, y=20, width=70, height=20,
        metadata={
            "source": "windows_ui_automation",
            "uia_runtime_id": runtime,
            "automation_id": "an-action",
            "uia_control_type": "button",
            "uia_visible": True,
            "uia_enabled": True,
            "uia_ancestor_context": ancestors,
            "document_scope": scope,
        },
    )


def selected_tab(name="OFR/4680-"):
    return ScreenElement(
        kind="tabitem", label=name, x=20, y=8, width=80, height=20,
        metadata={
            "source": "windows_ui_automation",
            "uia_runtime_id": "selected-doc",
            "uia_tab_scope": "document",
            "uia_selected": True,
            "uia_visible": True,
            "uia_enabled": True,
        },
    )


def test_unique_active_offer_toolbar_has_business_meaning_only_in_offer():
    original = button(scope="OFR/4680-")
    enriched = enrich_windowhub_scene(scene(selected_tab(), original))
    assert enriched.elements[1].label == "Dodaj"
    assert enriched.elements[1].metadata["semantic_label"] == "Dodaj nową pozycję okna do oferty"
    assert "semantic_label" not in original.metadata
    assert "semantic_label" not in enrich_windowhub_scene(
        scene(selected_tab(), original, title="Wielkość okna")
    ).elements[1].metadata


def test_multiple_add_buttons_are_scoped_to_selected_document():
    other1 = button("first", scope="OFR/4670-")
    active = button("second", scope="OFR/4680-")
    other2 = button("third", scope="OFR/4678-")
    result = enrich_windowhub_scene(scene(selected_tab(), other1, active, other2))
    assert "semantic_label" not in result.elements[1].metadata
    assert result.elements[2].metadata["semantic_label"] == "Dodaj nową pozycję okna do oferty"
    assert "semantic_label" not in result.elements[3].metadata


def test_unresolved_document_scope_never_invents_business_meaning():
    other = button("first", scope="OFR/4670-")
    unresolved = button("second", scope=None)
    result = enrich_windowhub_scene(scene(selected_tab(), other, unresolved))
    assert all("semantic_label" not in e.metadata for e in result.elements[1:])


def test_no_verified_document_tab_is_not_enough():
    original = button(scope="OFR/4680-")
    result = enrich_windowhub_scene(scene(original))
    assert "semantic_label" not in result.elements[0].metadata


def test_print_template_add_not_misclassified_as_construction():
    original = button(
        scope="OFR/4680-",
        ancestors=(("pane", "x", "Szablony wydruków"),),
    )
    result = enrich_windowhub_scene(scene(selected_tab(), original))
    assert "semantic_label" not in result.elements[1].metadata
