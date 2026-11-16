"""Verified semantic skills must be context-scoped and never cause a click."""
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene


def scene(*elements, title="Okna - OFR/4680-"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe", active_window_title=title
            ),
        ),
        elements=tuple(elements),
    )


def button(runtime="one", *, label="Dodaj", ancestors=()):
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
        },
    )


def test_unique_offer_toolbar_add_has_business_meaning_only_in_offer():
    original = button()
    enriched = enrich_windowhub_scene(scene(original))
    assert enriched.elements[0].label == "Dodaj"
    assert enriched.elements[0].metadata["semantic_label"] == "Dodaj nową pozycję okna do oferty"
    assert "semantic_label" not in original.metadata
    assert "semantic_label" not in enrich_windowhub_scene(
        scene(original, title="Wielkość okna")
    ).elements[0].metadata


def test_ambiguous_add_buttons_are_not_given_invented_business_meaning():
    original, alternate = button("one"), button("two")
    result = enrich_windowhub_scene(scene(original, alternate))
    assert all("semantic_label" not in e.metadata for e in result.elements)


def test_print_template_add_not_misclassified_as_construction():
    original = button(ancestors=(("pane", "x", "Szablony wydruków"),))
    result = enrich_windowhub_scene(scene(original))
    assert "semantic_label" not in result.elements[0].metadata
