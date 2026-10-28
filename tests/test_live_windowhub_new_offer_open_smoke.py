from types import SimpleNamespace

import pytest

from tools.live_windowhub_new_offer_open_smoke import (
    _initial_scene_problem,
    _plan_block_reason,
)


def _element(label, metadata, capability="clickable"):
    return SimpleNamespace(
        label=label,
        metadata=metadata,
        interaction_capability=SimpleNamespace(value=capability),
    )


def _action(name="click_screen_element", target="NOWA OFERTA", **kwargs):
    defaults = {
        "name": name,
        "target": target,
        "value": None,
        "requires_confirmation": False,
        "description": "Controlled test action",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _plan(*actions, requires_manual_review=False, completed=False):
    return SimpleNamespace(
        steps=tuple(SimpleNamespace(action=action) for action in actions),
        requires_manual_review=requires_manual_review,
        completed=completed,
    )


def _valid_scene():
    return SimpleNamespace(
        active_document="Start1",
        elements=(
            _element(
                "Start1",
                {
                    "uia_tab_scope": "document",
                    "uia_document_tab_selected": True,
                },
                capability="selectable",
            ),
            _element(
                "NOWA OFERTA",
                {
                    "source": "windowhub_ui_automation",
                    "uia_control_type": "button",
                    "uia_visible": True,
                    "uia_enabled": True,
                    "document_scope": "Start1",
                },
            ),
        ),
    )


def test_guard_allows_only_the_single_semantic_new_offer_click():
    assert _plan_block_reason(_plan(_action())) is None


@pytest.mark.parametrize(
    ("action", "message"),
    [
        (_action(name="write_text", target="NOWA OFERTA"), "non-click action"),
        (_action(target="OK"), "not NOWA OFERTA"),
        (_action(value="unexpected text"), "text value"),
        (_action(requires_confirmation=True), "requires confirmation"),
    ],
)
def test_guard_blocks_actions_outside_the_single_click_boundary(action, message):
    reason = _plan_block_reason(_plan(action))
    assert reason is not None
    assert message in reason


def test_guard_blocks_multi_action_plans():
    reason = _plan_block_reason(
        _plan(
            _action(),
            _action(name="click_screen_element", target="OK"),
        )
    )
    assert reason is not None
    assert "exactly one action" in reason


def test_guard_blocks_plans_that_require_manual_review_or_are_completed():
    assert _plan_block_reason(
        _plan(_action(), requires_manual_review=True)
    ) == "The proposed plan requires manual review."
    assert _plan_block_reason(
        _plan(_action(), completed=True)
    ) == "The reasoner marked the goal complete without an action."


def test_preflight_accepts_active_start1_and_unique_uia_button():
    assert _initial_scene_problem(_valid_scene()) is None


def test_preflight_blocks_when_start1_is_not_active():
    scene = _valid_scene()
    scene.active_document = "OFR/4005"
    reason = _initial_scene_problem(scene)
    assert reason is not None
    assert "Start1 is not the active document" in reason


def test_preflight_allows_missing_uia_selection_when_active_document_is_verified():
    scene = _valid_scene()
    scene.elements = (
        _element(
            "Start1",
            {"uia_tab_scope": "document"},
            capability="selectable",
        ),
        scene.elements[1],
    )
    assert _initial_scene_problem(scene) is None


def test_preflight_blocks_when_start1_selection_conflicts_with_active_document():
    scene = _valid_scene()
    scene.elements = (
        _element(
            "Start1",
            {
                "uia_tab_scope": "document",
                "uia_document_tab_selected": False,
            },
            capability="selectable",
        ),
        scene.elements[1],
    )
    reason = _initial_scene_problem(scene)
    assert reason is not None
    assert "selection conflicts" in reason


@pytest.mark.parametrize("scope", ["OFR/4005", None])
def test_preflight_blocks_missing_or_conflicting_offer_document_scope(scope):
    scene = _valid_scene()
    button = scene.elements[1]
    metadata = dict(button.metadata)
    if scope is None:
        metadata.pop("document_scope", None)
    else:
        metadata["document_scope"] = scope
    scene.elements = (scene.elements[0], _element("NOWA OFERTA", metadata))

    reason = _initial_scene_problem(scene)

    assert reason is not None
    assert "document_scope does not match" in reason


def test_preflight_blocks_duplicate_or_non_uia_offer_targets():
    scene = _valid_scene()
    button = scene.elements[1]
    scene.elements = scene.elements + (
        _element(
            "Nowa oferta",
            dict(button.metadata),
        ),
    )
    reason = _initial_scene_problem(scene)
    assert reason is not None
    assert "Expected one visible, enabled, UIA-grounded" in reason


def test_preflight_blocks_if_the_initial_offer_dialog_is_already_open():
    scene = _valid_scene()
    scene.elements = scene.elements + (
        _element(
            "OK",
            {
                "uia_owned_modal": True,
                "uia_visible": True,
            },
        ),
        _element(
            "Anuluj",
            {
                "uia_owned_modal": True,
                "uia_visible": True,
            },
        ),
    )
    reason = _initial_scene_problem(scene)
    assert reason is not None
    assert "already open" in reason
