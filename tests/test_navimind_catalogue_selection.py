"""Native UIA catalogue selections require a source-exact item AND owner."""
from types import SimpleNamespace as NS

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.navimind_catalogue_selection import (
    prepare_exact_catalogue_pick, verify_exact_catalogue_readback,
)


def scene(stage="Podstawowe parametry okna", *,
          value="Weiss", option="Weiss", native_parent=True,
          other_runtime=False, duplicate=False, source="windows_ui_automation"):
    combo_rid = "combo-right"
    combo = ScreenElement(
        kind="combobox", label="Wybierz kolor profili",
        metadata={
            "source": source, "uia_visible": True, "uia_enabled": True,
            "automation_id": "1054", "uia_runtime_id": combo_rid,
            "current_value": value,
            "current_value_source": "get_value",
        },
    )
    option_item = ScreenElement(
        kind="listitem", label=option,
        metadata={
            "source": "windows_ui_automation",
            "uia_visible": True, "uia_enabled": True,
            "uia_runtime_id": "option-1",
            "uia_ancestor_structure": (
                {"control_type": "combobox", "automation_id": "1054",
                 "runtime_id": ("combo-wrong" if other_runtime else combo_rid)},
            ) if native_parent else (),
        },
    )
    elements = (combo, option_item)
    if duplicate:
        elements += (option_item,)
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title=stage,
            ),
        ),
        elements=elements,
    )


def current(*, inside="Weiss", outside="Weiss"):
    return NS(
        position_id="S01-P001", product_type="window",
        catalogue_requirements=(
            ("color_inside", inside), ("color_outside", outside),
        ),
    )


def option(label="Weiss"):
    return NS(label=label, role="listitem", uia_runtime_id="option-1")


def test_source_exact_option_native_parent_and_postselection_readback():
    previous = scene(value="Anthrazit")
    pick, reason = prepare_exact_catalogue_pick(
        previous, current(), option(),
    )
    assert pick is not None, reason
    assert pick.field_name == "profile_color"
    assert pick.position_id == "S01-P001"
    assert verify_exact_catalogue_readback(scene(value="Weiss"), pick)[0]


def test_wrong_color_or_source_side_ambiguity_never_authorizes_click():
    assert prepare_exact_catalogue_pick(
        scene(), current(inside="Weiss", outside="Anthrazit"),
        option(),
    )[0] is None
    assert prepare_exact_catalogue_pick(
        scene(), current(), option("Anthrazit"),
    )[0] is None


def test_reused_automation_id_but_wrong_parent_runtime_is_blocked():
    assert prepare_exact_catalogue_pick(
        scene(other_runtime=True), current(), option(),
    )[0] is None
    assert prepare_exact_catalogue_pick(
        scene(native_parent=False), current(), option(),
    )[0] is None


def test_duplicate_native_option_does_not_silently_resolve():
    assert prepare_exact_catalogue_pick(
        scene(duplicate=True), current(), option(),
    )[0] is None


def test_postselection_value_must_match_not_merely_a_changed_scene():
    pick, _ = prepare_exact_catalogue_pick(
        scene(value="Anthrazit"), current(), option(),
    )
    assert pick is not None
    assert not verify_exact_catalogue_readback(
        scene(value="Anthrazit"), pick,
    )[0]
    assert not verify_exact_catalogue_readback(
        scene(value="Weiss", source="computer_vision"), pick,
    )[0]
    assert not verify_exact_catalogue_readback(
        scene(stage="Parametry szklenia", value="Weiss"), pick,
    )[0]
