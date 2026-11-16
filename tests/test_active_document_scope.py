"""MDI scope must be proven before exposing duplicate per-offer actions."""
from app.agent.runtime.active_document_scope import (
    selected_document_tab, duplicate_document_action_status,
    unique_active_document_control,
)
from tests.test_windowhub_offer_semantic_skill import scene, button, selected_tab


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
