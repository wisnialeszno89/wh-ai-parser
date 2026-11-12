import pytest

from tools import transfer_offer_draft_lab as lab
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


def test_photo_failure_stops_before_opening_form_and_preserves_output(tmp_path, monkeypatch, capsys):
    import tkinter

    photo = tmp_path / "offer.jpg"
    output = tmp_path / "existing.json"
    output.write_text("existing", encoding="utf-8")

    def fail_ocr(path, *, tesseract):
        assert path == photo
        assert tesseract == "local-tesseract"
        raise ValueError("Pozycja 20.0: nieczytelny wymiar")

    monkeypatch.setattr(lab, "read_german_offer_photo_file", fail_ocr)
    monkeypatch.setattr(tkinter, "Tk", lambda: pytest.fail("Formularz otworzył się po błędzie OCR."))

    assert lab.main(["--photo", str(photo), "--output", str(output), "--tesseract", "local-tesseract"]) == 2
    assert output.read_text(encoding="utf-8") == "existing"
    assert "Pozycja 20.0: nieczytelny wymiar" in capsys.readouterr().err


def test_mail_draft_transfers_all_manual_descriptions_without_filling_prices():
    from tools.check_windowhub_mixed_offer import mail_positions, prepare_mixed_offer

    example = lab.ROOT / "examples" / "windowhub-shading-mail.txt"
    draft = prepare_mixed_offer(mail_positions(example.read_text(encoding="utf-8")))
    planned = plan_lab_transfer(draft, set())
    saved = serialize_form_rows(map(form_values, planned))

    assert len(saved) == 13
    for source, target in zip(draft["positions"], saved):
        assert target["reference"] == source["position"]
        assert target["description"] == source["description"]
        assert target["execution"] == "manual"
        assert target.get("quantity") == source["quantity"]
        assert target["price"] is None
    assert all("quantity" not in row for row in saved[-2:])


def test_manual_transfer_rejects_mixed_rows_instead_of_omitting_them():
    draft = {"status": "sales_review_required", "positions": [
        {"position": "MAIL-01", "status": "manual", "execution": "manual", "description": "ZIP"},
        {"position": "MAIL-02", "status": "planned"},
    ]}
    with pytest.raises(ValueError, match="wyłącznie szkice z pozycjami ręcznymi"):
        plan_lab_transfer(draft, set())
