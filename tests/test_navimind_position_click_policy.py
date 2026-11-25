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
        "S01-P001", field_name, value, "verified-native-field-state",
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
