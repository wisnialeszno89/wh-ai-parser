"""Offline source-scoped native wizard navigation guard."""
from types import SimpleNamespace as NS

from app.agent.runtime.navimind_position_click_policy import (
    allowed_position_click,
)
from app.agent.runtime.navimind_work_mission import PositionFieldReceipt


def target(label, role="button", automation_id=None):
    return NS(label=label, role=role, automation_id=automation_id)


def proof(field_name, value):
    return PositionFieldReceipt(
        "S01-P001", field_name, value, "verified-native-field-state", "rid-"+field_name,
    )


def attempt(stage, button, *, receipts=(), position_id="S01-P001"):
    return allowed_position_click(
        stage=stage, target=button,
        current_position=NS(
            position_id=position_id, product_type="window",
        ),
        field_receipts=receipts,
    )


def test_only_native_mdi_verified_add_and_exact_window_type_can_be_proposed():
    assert attempt("offer_document", target("Dodaj"))[0]
    assert not attempt("offer_document", target("Usuń"))[0]
    assert attempt("position", target("Okno", "radiobutton", "1329"))[0]
    assert not attempt("position", target("Drzwi", "radiobutton", "1335"))[0]


def test_next_cannot_advance_without_fresh_quantity_receipt():
    button = target("Dalej >", "button", "12324")
    assert not attempt("position", button)[0]
    assert attempt("position", button, receipts=(proof("quantity_input", "2"),))[0]
    assert not attempt(
        "position", button,
        receipts=(NS(
            position_id="S01-P002", field_name="quantity_input",
            value="2", signature="not-current",
        ),),
    )[0]


def test_dimensions_next_requires_both_correct_position_proofs():
    button = target("Dalej >", "button", "12324")
    assert not attempt("dimensions", button, receipts=(proof("width_1", "1500"),))[0]
    assert attempt(
        "dimensions", button,
        receipts=(proof("width_1", "1500"), proof("height_1", "1400")),
    )[0]
    assert not attempt(
        "dimensions", target("Dalej >", "button", "WRONG-ID"),
        receipts=(proof("width_1", "1500"), proof("height_1", "1400")),
    )[0]


def test_unlearned_catalogue_or_finish_requires_human():
    for stage in ("basic_parameters", "glazing", "hardware", "modifier"):
        assert not attempt(
            stage, target("Wybierz system profili", "button"),
            receipts=(proof("quantity_input", "2"),),
        )[0]
        assert not attempt(
            stage, target("Zakończ", "button"),
            receipts=(proof("quantity_input", "2"),),
        )[0]


def test_other_product_type_is_never_borrowed_as_window():
    permitted, reason = allowed_position_click(
        stage="position", target=target("Okno", "radiobutton", "1329"),
        current_position=NS(position_id="S01-P001", product_type="sliding_door"),
    )
    assert not permitted and reason == "product_type_not_supported_by_pilot"


def native_scene(title, fields):
    from app.agent.environment.environment_observation import EnvironmentObservation
    from app.agent.environment.environment_state import EnvironmentState
    from app.agent.perception.screen_scene import ScreenScene
    from app.agent.perception.screen_element import ScreenElement
    elements = tuple(
        ScreenElement(kind="edit", label=label, metadata={
            "source": "windowhub_ui_automation",
            "automation_id": automation_id,
            "uia_runtime_id": "rid-" + field,
            "uia_visible": True, "uia_enabled": True,
            "current_value": value,
            "current_value_source": "get_value",
        })
        for field, label, automation_id, value in fields
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe", active_window_title=title,
            ),
        ), elements=elements,
    )


def test_position_next_rechecks_native_quantity_not_just_cached_receipt():
    from app.agent.runtime.navimind_position_click_policy import (
        verify_position_navigation_readback,
    )
    button = target("Dalej >", "button", "12324")
    current = NS(position_id="S01-P001", product_type="window")
    receipts = (proof("quantity_input", "2"),)
    okay = native_scene(
        "Dodawanie nowej pozycji",
        (("quantity_input", "Ile sztuk", "1001", "2"),),
    )
    changed = native_scene(
        "Dodawanie nowej pozycji",
        (("quantity_input", "Ile sztuk", "1001", "3"),),
    )
    assert verify_position_navigation_readback(
        okay, stage="position", target=button,
        current_position=current, field_receipts=receipts,
    )[0]
    assert not verify_position_navigation_readback(
        changed, stage="position", target=button,
        current_position=current, field_receipts=receipts,
    )[0]


def test_dimensions_next_rechecks_both_native_values_after_human_change():
    from app.agent.runtime.navimind_position_click_policy import (
        verify_position_navigation_readback,
    )
    button = target("Dalej >", "button", "12324")
    current = NS(position_id="S01-P001", product_type="window")
    receipts = (proof("width_1", "1500"), proof("height_1", "1400"))
    base = (
        ("width_1", "Szerokość", "1000", "1500"),
        ("height_1", "Wysokość", "1001", "1400"),
    )
    okay = native_scene("Wielkość okna", base)
    changed = native_scene("Wielkość okna", (
        ("width_1", "Szerokość", "1000", "1500"),
        ("height_1", "Wysokość", "1001", "1450"),
    ))
    assert verify_position_navigation_readback(
        okay, stage="dimensions", target=button,
        current_position=current, field_receipts=receipts,
    )[0]
    assert not verify_position_navigation_readback(
        changed, stage="dimensions", target=button,
        current_position=current, field_receipts=receipts,
    )[0]


def test_native_default_quantity_one_allows_next_without_rewriting_same_value():
    from app.agent.runtime.navimind_position_click_policy import (
        verify_position_navigation_readback,
    )
    current = NS(
        position_id="S01-P001", product_type="window",
        quantity=1, width_mm=1500, height_mm=1400,
    )
    native = native_scene(
        "Dodawanie nowej pozycji",
        (("quantity_input", "Ile sztuk", "1001", "1"),),
    )
    result = verify_position_navigation_readback(
        native, stage="position",
        target=target("Dalej >", "button", "12324"),
        current_position=current, field_receipts=(),
    )
    assert result[0]


def test_native_default_dimensions_must_match_source_before_next():
    from app.agent.runtime.navimind_position_click_policy import (
        verify_position_navigation_readback,
    )
    current = NS(
        position_id="S01-P001", product_type="window",
        quantity=1, width_mm=1500, height_mm=1400,
    )
    correct = native_scene("Wielkość okna", (
        ("width_1", "Szerokość", "1000", "1500"),
        ("height_1", "Wysokość", "1001", "1400"),
    ))
    wrong = native_scene("Wielkość okna", (
        ("width_1", "Szerokość", "1000", "1550"),
        ("height_1", "Wysokość", "1001", "1400"),
    ))
    button = target("Dalej >", "button", "12324")
    assert verify_position_navigation_readback(
        correct, stage="dimensions", target=button,
        current_position=current, field_receipts=(),
    )[0]
    assert not verify_position_navigation_readback(
        wrong, stage="dimensions", target=button,
        current_position=current, field_receipts=(),
    )[0]
