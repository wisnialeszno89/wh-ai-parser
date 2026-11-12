import json
import sys
from pathlib import Path

import pytest

from tools.check_windowhub_mixed_offer import main, mail_positions, prepare_mixed_offer, request_positions, sample_positions

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


def test_mail_preserves_stulp_pair_and_common_preferences_without_guessing():
    text = (
        "Fenster Dreifach Verglasung\nSchmales Profil\nWeiß/Anthrazit\n\n"
        "1590 x 960 stulp\n1590 x 960 ohne Stulp"
    )
    report = prepare_mixed_offer(mail_positions(text))
    with_stulp, without_stulp = report["positions"]

    assert with_stulp["source"]["mullion_requirement"] == "movable"
    assert without_stulp["source"]["mullion_requirement"] == "without_movable"
    for entry in (with_stulp, without_stulp):
        row = entry["source"]
        assert (row["width_mm"], row["height_mm"]) == (1590, 960)
        assert (row["glazing_panes"], row["profile_preference"], row["color_pair"]) == (3, "narrow", "Weiß/Anthrazit")
        assert row["variant_group"] == 1
        assert row["quantity"] is None and row["layout"] is None and row["opening"] is None
        assert row["color_inside"] is None and row["color_outside"] is None
        assert entry["status"] == "review"
        assert entry["proposal"]["kind"] == "comparison_variant"
        assert entry["proposal"]["group"] == 1
        assert entry["proposal"]["sash_count"] == 2
        assert "Potwierdź ilość" in entry["reason"]
        assert "steps" not in entry
    assert with_stulp["proposal"]["mullion"] == "movable"
    assert without_stulp["proposal"]["mullion"] == "fixed"
    assert without_stulp["source"]["mullion_requirement"] == "without_movable"


def test_mail_does_not_copy_a_common_quantity_to_both_stulp_variants():
    text = "2 Stk. Fenster\n1590 x 960 mit Stulp\n1590 x 960 ohne Stulp"

    assert [row["quantity"] for _, row in mail_positions(text)] == [None, None]


def test_mail_distinguishes_tilt_only_from_tilt_turn_and_conflicting_request():
    example = EXAMPLE.with_name("windowhub-tilt-mail.txt")
    report = prepare_mixed_offer(mail_positions(example.read_text(encoding="utf-8")))
    tilt, tilt_turn, conflict = report["positions"]

    assert tilt["status"] == "planned"
    assert [step["tool"] for step in tilt["steps"]] == ["FRAME", "SASH", "GLASS", "HARDWARE"]
    assert tilt["steps"][1]["parameters"]["opening"] == "tilt"
    assert tilt["steps"][-1]["parameters"] == {"opening": "tilt"}
    assert tilt["review_notes"]
    assert tilt_turn["status"] == "simulated"
    assert tilt_turn["simulation"]["final_direction"] == "RIGHT"
    assert conflict["status"] == "review"
    assert "sprzeczny" in conflict["reason"]


def test_only_plans_a_single_sash_when_confirmed_for_tilt():
    text = (
        "Fenster 1 Stk. nur kippbar, einflügelig, 800 x 600 mm\n"
        "Kippfenster 1 Stk. zweiflügelig, 800 x 600 mm\n"
        "Fenster 1 Stk. nicht nur kippbar, 800 x 600 mm"
    )
    report = prepare_mixed_offer(mail_positions(text))
    assert [row["status"] for row in report["positions"]] == ["planned", "review", "review"]


def test_psk_mail_keeps_sash_position_separate_from_its_slide_direction():
    example = EXAMPLE.with_name("windowhub-psk-mail.txt")
    report = prepare_mixed_offer(mail_positions(example.read_text(encoding="utf-8")))
    left, right, missing = report["positions"]

    assert [row["status"] for row in (left, right, missing)] == ["planned", "planned", "review"]
    assert (left["plan"]["hardware"]["target_side"], left["plan"]["slide_direction"]) == ("RIGHT", "LEFT")
    assert (right["plan"]["hardware"]["target_side"], right["plan"]["slide_direction"]) == ("LEFT", "RIGHT")
    assert left["plan"]["fields"][0] == {"side": "LEFT", "role": "fixed", "field_width_mm": 1150}
    assert "kierunku przesuwu" in missing["reason"]


@pytest.mark.parametrize(("details", "reason"), [
    ("Schieberichtung: links", "widok odniesienia"),
    ("Innenansicht, Schieberichtung: rechts", "w stronę pola stałego"),
    ("Innenansicht, Schieberichtung: links/rechts", "kierunku przesuwu"),
    ("Innenansicht, Schieberichtung: links, HST", "sprzeczny"),
])
def test_psk_mail_blocks_ambiguous_or_conflicting_configuration(details, reason):
    mail = "PSK-Tür 1 Stk. FIX+PSK 2400 x 2100 mm\nTeilung: 1150 mm von links\n" + details
    (entry,) = prepare_mixed_offer(mail_positions(mail))["positions"]

    assert entry["status"] == "review"
    assert reason in entry["reason"]
    assert "plan" not in entry


def test_five_position_request_preserves_per_item_finishes_and_glazing(monkeypatch, tmp_path):
    example = EXAMPLE.with_name("windowhub-five-position-request.json")
    output = tmp_path / "draft.json"
    monkeypatch.setattr(sys, "argv", ["check_windowhub_mixed_offer.py", "--request-file", str(example), "--output", str(output)])
    assert main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    first, double, stulp, door, balcony = report["positions"]

    assert [row["status"] for row in report["positions"]] == ["simulated"] * 5
    assert [row["position"] for row in report["positions"]] == ["01", "02", "03", "04", "05"]
    assert first["quantity"] == first["source"]["quantity"] == 2
    scene = first["simulation"]["scene"]
    assert scene["opening"] == {"width": 1000, "height": 1010}
    assert [item["kind"] for item in scene["elements"]] == ["FRAME", "SASH", "GLASS"]
    assert scene["elements"][1]["direction"] == "LEFT"
    assert scene["elements"][2]["panes"] == 2
    assert first["steps"][0]["parameters"] == {"width_mm": 1000, "height_mm": 1010}
    assert first["steps"][2]["parameters"] == {"panes": 2}
    assert first["steps"][3]["parameters"]["direction"] == "LEFT"
    assert [row["source"]["color_pair"] for row in (first, double, stulp)] == ["mahoń/białe"] * 3
    assert double["source"]["split_from_left_mm"] == 755
    assert double["simulation"]["final_directions"] == {"left": "LEFT", "right": "RIGHT"}
    assert "dkr 1510x1400 dkl/dkr" in double["source"]["source_text"]
    assert stulp["simulation"]["active_side"] == "left"
    assert stulp["simulation"]["passive_side"] == "right"
    assert door["source"]["opening"] == "DL" and "glazing_panes" not in door["source"]
    assert door["source"]["test_assumptions"] == ["swing", "infill"]
    assert (door["simulation"]["direction"], door["simulation"]["swing"]) == ("LEFT", "inward")
    assert balcony["source"]["color"] == "biały" and "color_pair" not in balcony["source"]
    assert balcony["source"]["glazing_panes"] == 2
    assert balcony["source"]["test_assumptions"] == ["single_sash_confirmed", "swing", "threshold"]
    assert balcony["simulation"]["threshold"] == "standard"
    assert report["status"] == "sales_review_required"


@pytest.mark.parametrize(("threshold", "opening", "direction", "inverted"), [
    ("standard", "DKR", "RIGHT", True),
    ("low", "DKR", "RIGHT", True),
    ("low", "DKL", "LEFT", False),
])
def test_balcony_reads_back_threshold_glazing_and_opening(threshold, opening, direction, inverted):
    example = EXAMPLE.with_name("windowhub-five-position-request.json")
    row = json.loads(example.read_text(encoding="utf-8"))["positions"][-1]
    row.update(threshold=threshold, opening=opening)
    (entry,) = prepare_mixed_offer([("balcony_window", row)])["positions"]

    assert entry["status"] == "simulated"
    scene = entry["simulation"]["scene"]
    assert scene["opening"] == {"width": 1010, "height": 2100}
    frame, sill, sash, glass = scene["elements"]
    assert (sill["kind"], sill["threshold"], sill["parent_id"]) == ("THRESHOLD", threshold, frame["id"])
    assert (sash["opening"], sash["direction"], sash["inversion_checked"]) == ("TILT_TURN", direction, inverted)
    assert (glass["panes"], glass["parent_id"]) == (2, sash["id"])
    stages = ["frame", "threshold", "sash", "glazing", "hardware"]
    assert [step["stage"] for step in entry["simulation"]["trace"]] == stages + (["inversion"] if inverted else [])


@pytest.mark.parametrize(("field", "value", "reason"), [
    ("threshold", None, "progu"),
    ("threshold", "unknown", "progu"),
    ("single_sash_confirmed", False, "skrzydło"),
    ("swing", "outward", "do wewnątrz"),
    ("glazing_panes", True, "szyb"),
])
def test_balcony_leaves_incomplete_or_unsupported_configuration_for_review(field, value, reason):
    example = EXAMPLE.with_name("windowhub-five-position-request.json")
    row = json.loads(example.read_text(encoding="utf-8"))["positions"][-1]
    row[field] = value
    (entry,) = prepare_mixed_offer([("balcony_window", row)])["positions"]

    assert entry["status"] == "review"
    assert reason in entry["reason"]
    assert "simulation" not in entry


def test_hst_psk_and_arch_stay_separate_in_one_mail():
    example = EXAMPLE.with_name("windowhub-sliding-arch-mail.txt")
    report = prepare_mixed_offer(mail_positions(example.read_text(encoding="utf-8")))
    hst_right, psk, hst_left, arch, door = report["positions"]

    assert [row["status"] for row in report["positions"]] == ["planned", "planned", "planned", "review", "review"]
    assert hst_right["plan"]["hardware"] == {"family": "HST", "target_side": "RIGHT"}
    assert hst_right["plan"]["slide_direction"] == "LEFT"
    assert psk["plan"]["hardware"] == {"family": "PSK", "target_side": "LEFT"}
    assert hst_left["plan"]["hardware"] == {"family": "HST", "target_side": "LEFT"}
    assert hst_left["plan"]["slide_direction"] == "RIGHT"
    assert arch["source"]["arch_rise_mm"] == 600
    assert "łuku" in arch["reason"] and "plan" not in arch
    assert door["source"]["opening_spec"] == {"type": "turn", "direction": "LEFT"}


def test_confirmed_single_sash_uses_window_r_shorthand_in_the_simulator():
    (position,) = prepare_mixed_offer(mail_positions("Fenster 1 Stk. F004 DK-Fenster R, 1000 x 1000 mm"))["positions"]

    assert position["status"] == "simulated"
    assert position["simulation"]["final_direction"] == "RIGHT"


def test_tilt_turn_window_without_single_sash_confirmation_stays_planned():
    row = {"position": "01", "quantity": 2, "width_mm": 1000, "height_mm": 1010,
           "opening": "DKL", "glazing_panes": 2}
    (position,) = prepare_mixed_offer([("tilt_turn_window", row)])["positions"]

    assert position["status"] == "planned"
    assert position["quantity"] == 2
    assert "simulation" not in position


def test_shading_mail_saves_descriptive_unpriced_positions(monkeypatch, tmp_path):
    example = EXAMPLE.with_name("windowhub-shading-mail.txt")
    output = tmp_path / "shading.json"
    monkeypatch.setattr(sys, "argv", ["check_windowhub_mixed_offer.py", "--mail-file", str(example), "--output", str(output)])

    assert main() == 0
    draft = json.loads(output.read_text(encoding="utf-8"))
    zip_line, *rollers, ten_channel, one_channel = draft["positions"]

    assert draft["status"] == "sales_review_required"
    assert all(row["status"] == "manual" and row["price"] is None for row in draft["positions"])
    assert zip_line["quantity"] == 2
    assert "Funk ohne Solar" in zip_line["description"]
    assert "Kabelausgang links und rechts" in zip_line["description"]
    assert len(rollers) == 10 and all(row["quantity"] == 1 for row in rollers)
    assert [row["source"]["width_mm"] for row in rollers].count(1930) == 2
    assert [row["source"]["width_mm"] for row in rollers].count(920) == 2
    assert all("Anthrazit" in row["description"] and "Solar" in row["description"] for row in rollers)
    assert [row["source"]["width_mm"] for row in rollers if "LHTF" in row["description"]] == [925, 915]
    assert [row["source"]["width_mm"] for row in rollers if "Gurtführung" in row["description"]] == [2740]
    assert "mit Steuerung" in ten_channel["description"]
    assert ten_channel["quantity"] is one_channel["quantity"] is None


def test_shading_without_dimensions_survives_in_mixed_mail():
    text = "ZIP-Anlagen\nRAL 9007 Struktur\nFenster 1 Stk. F004 DK-Fenster R, 1000 x 1000 mm"
    shading, window = prepare_mixed_offer(mail_positions(text))["positions"]

    assert shading["status"] == "manual"
    assert shading["quantity"] is shading["source"]["width_mm"] is shading["price"] is None
    assert "RAL 9007 Struktur" in shading["description"]
    assert window["status"] == "simulated"
