import pytest

from tools.transfer_offer_draft_lab import form_values, parse_requested_discount, plan_lab_transfer, serialize_form_rows


def source_draft():
    return {
        "status": "technical_draft",
        "positions": [
            {
                "position": reference, "quantity": 1, "width_mm": width, "height_mm": 1145,
                "system": "Zirkon", "construction": "F004 DK-Fenster", "header_code": "EP",
                "opening": opening, "note_code": "WKÜ",
                "cover_strip": {"material": "Aluminium", "side": "outside", "sides": 3, "size_mm": "2x30"},
            }
            for reference, width, opening in [("10.0", 935, "DKL"), ("20.0", 935, "DKR"), ("30.0", 1030, "DKR")]
        ],
        "excluded": [{"position": "11.0", "reason": "zero_quantity"}],
    }


def test_transfer_keeps_remaining_configurations_and_appends_unpriced_manual_line():
    planned = plan_lab_transfer(source_draft(), {"20.0"})
    first, third, manual = serialize_form_rows(map(form_values, planned))

    assert [row["reference"] for row in (first, third, manual)] == ["10.0", "30.0", "20.0"]
    assert (first["execution"], first["opening"], first["strip_size_mm"]) == ("configure", "DKL", "2x30")
    assert (third["execution"], third["opening"], third["width_mm"]) == ("configure", "DKR", 1030)
    assert manual.keys() == {"reference", "execution", "description", "price"}
    assert manual["execution"] == "manual"
    assert manual["price"] is None
    assert "DKR" in manual["description"] and "935 × 1145 mm" in manual["description"]


def test_simulation_rejects_unknown_position_and_incomplete_source():
    draft = source_draft()
    with pytest.raises(ValueError, match="spoza szkicu"):
        plan_lab_transfer(draft, {"11.0"})
    draft["positions"][1]["width_mm"] = True
    with pytest.raises(ValueError, match="20.0.*width_mm"):
        plan_lab_transfer(draft, set())


def test_discount_distinguishes_no_instruction_from_explicit_zero():
    assert parse_requested_discount(None) is None
    assert parse_requested_discount("0") == "0"
    assert parse_requested_discount("5,50") == "5.5"


@pytest.mark.parametrize("value", ["", "-5", "100.01", "5.555", "5%", "NaN"])
def test_discount_rejects_invalid_instructions(value):
    with pytest.raises(ValueError, match="Rabat"):
        parse_requested_discount(value)
