import json
from pathlib import Path

import pytest

from tools.check_windowhub_mixed_offer import mail_positions, prepare_mixed_offer, request_positions, sample_positions

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/windowhub-mixed-request.json"
MAIL_EXAMPLE = EXAMPLE.with_name("windowhub-mixed-mail.txt")


def test_mixed_handoff_continues_after_incomplete_position():
    source = {"status": "technical_draft", "positions": [{
        "position": "10.0", "construction": "F004 DK-Fenster", "system": "Zirkon",
        "width_mm": 935, "height_mm": 1145, "quantity": 1, "opening": "DKL",
    }]}
    single, complete, incomplete = sample_positions(source)

    report = prepare_mixed_offer([single, incomplete, complete])
    first, second, third = report["positions"]

    assert report["status"] == "sales_review_required"
    assert first["status"] == "simulated"
    assert first["source"] == source["positions"][0]
    assert first["simulation"]["final_direction"] == "LEFT"
    assert second["status"] == "review"
    assert "Brakuje wymiaru podziału" in second["reason"]
    assert "steps" not in second
    assert third["status"] == "planned"
    assert third["steps"][1]["parameters"]["offset_from_left_mm"] == 650
    assert third["steps"][-1]["side"] == "RIGHT"


def test_one_request_file_controls_layout_and_handoff():
    request = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    report = prepare_mixed_offer(request_positions(request))
    single, incomplete, planned = report["positions"]

    assert single["source"]["cover_strip"]["size_mm"] == "2x30"
    assert incomplete["status"] == "review"
    assert planned["steps"][-1]["side"] == "LEFT"
    assert planned["steps"][-1]["parameters"]["opening_code"] == "DKR"


def test_request_rejects_duplicate_position_identifiers():
    with pytest.raises(ValueError, match="Powtórzony identyfikator"):
        request_positions({"positions": [{"position": "1"}, {"position": "1"}]})


def test_invalid_field_in_one_request_position_does_not_block_next():
    request = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    request["positions"][0]["opening"] = ["DKL", "DKR"]

    report = prepare_mixed_offer(request_positions(request))

    assert report["positions"][0]["status"] == "review"
    assert "Pole opening" in report["positions"][0]["reason"]
    assert report["positions"][-1]["status"] == "planned"


def test_german_mail_flows_into_the_same_sales_review_report():
    report = prepare_mixed_offer(mail_positions(MAIL_EXAMPLE.read_text(encoding="utf-8")))
    first, second, third = report["positions"]

    assert report["status"] == "sales_review_required"
    assert first["status"] == "simulated"
    assert second["status"] == "review"
    assert "Brakuje wymiaru podziału" in second["reason"]
    assert third["status"] == "planned"
    assert third["source"]["quantity"] == 2
    assert third["steps"][-1]["side"] == "LEFT"
    assert third["steps"][-1]["parameters"]["opening_code"] == "DKR"


def test_mail_keeps_door_and_more_complex_layout_in_review():
    text = "Haustür DL\n950 x 2070\nFenster 1 Stk. FIX+RU+FIX, DKL\n1600 x 1400\nTeilung: 650 mm von links"
    report = prepare_mixed_offer(mail_positions(text))
    door, window = report["positions"]

    assert door["status"] == window["status"] == "review"
    assert door["source"]["source_lines"][0] == "Haustür DL"
    assert window["source"]["layout"] == "FIX+RU+FIX"
    assert "steps" not in window
