"""MDI scope must be proven before exposing duplicate per-offer actions."""
from app.agent.runtime.active_document_scope import (
    selected_document_tab, duplicate_document_action_status,
    unique_active_document_control,
)
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.screen_element import ScreenElement


def scene(*elements):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="Okna.exe", active_window_title="Okna - OFR/4680-")
        ),
        elements=tuple(elements),
    )


def button(runtime, *, scope=None, ancestors=()):
    return ScreenElement(
        kind="button", label="Dodaj", x=10, y=20, width=40, height=20,
        metadata={
            "source": "windows_ui_automation", "uia_visible": True,
            "uia_enabled": True, "uia_runtime_id": runtime,
            "document_scope": scope, "uia_ancestor_context": ancestors,
        },
    )


def selected_tab(label="OFR/4680-"):
    return ScreenElement(
        kind="tabitem", label=label, x=10, y=5, width=70, height=20,
        metadata={
            "source": "windows_ui_automation", "uia_visible": True,
            "uia_tab_scope": "document", "uia_selected": True,
        },
    )


def test_selected_mdi_tab_does_not_prove_unscoped_toolbar_buttons():
    s = scene(
        selected_tab("OFR/4680-"),
        button("a", scope=None),
        button("b", scope=None),
        button("c", scope=None),
    )
    status = duplicate_document_action_status(s)
    assert selected_document_tab(s) == ("OFR/4680-", "verified_selected_document_tab")
    assert status["observed"] == 3
    assert status["unresolved_scope"] == 3
    assert status["safe_unique_active_target"] is False
    assert unique_active_document_control(s) is None


def test_one_proven_active_document_button_among_multiple_offers():
    active = button("b", scope="OFR/4680-")
    s = scene(
        selected_tab("OFR/4680-"),
        button("a", scope="OFR/4670-"),
        active,
        button("c", scope="OFR/4678-"),
    )
    status = duplicate_document_action_status(s)
    assert status["active_scope_proven"] == 1
    assert status["other_document_scope"] == 2
    assert status["safe_unique_active_target"] is True
    assert unique_active_document_control(s) is active


def test_duplicate_active_document_buttons_are_unsafe():
    s = scene(
        selected_tab(), button("a", scope="OFR/4680-"),
        button("b", scope="OFR/4680-"),
    )
    assert duplicate_document_action_status(s)["safe_unique_active_target"] is False
    assert unique_active_document_control(s) is None


def test_unproven_selected_tab_blocks_even_scoped_toolbar():
    s = scene(button("a", scope="OFR/4680-"))
    assert duplicate_document_action_status(s)["safe_unique_active_target"] is False
    assert unique_active_document_control(s) is None


def test_print_template_buttons_excluded():
    s = scene(
        selected_tab(),
        button("a", scope="OFR/4680-", ancestors=(
            ("pane", "x", "Szablony wydruków"),
        )),
    )
    assert duplicate_document_action_status(s)["observed"] == 0
    assert unique_active_document_control(s) is None
