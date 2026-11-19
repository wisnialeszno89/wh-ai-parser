"""Real enquiry regression: dry-run only, not a WindowHub GUI acceptance."""
import copy
import json
from pathlib import Path

from tools.prepare_windowhub_enquiry_mission import DEFAULT, plan_review, validate_mission


def mission():
    return json.loads(Path(DEFAULT).read_text(encoding="utf-8"))


def test_exact_customer_four_windows_two_marked_boxes():
    data = mission()
    result = plan_review(data)
    assert result["customer"] == "Top Trans Janik Artur"
    assert result["planned_window_count"] == 4
    assert result["planned_roller_box_count"] == 2
    assert result["planned_discount_percent"] == 20
    assert result["windowhub_offer_created"] is False
    assert result["windowhub_offer_saved"] is False
    assert data["positions"][0]["sections_width_mm"] == [820, 820]
    assert sum(row["width_mm"] for row in data["positions"]) == 4720
    assert [row["height_mm"] for row in data["positions"]] == [1010, 1010, 950, 980]
    assert data["global"]["bottom_transport_or_foot_strips"].startswith("exclude")
    assert [r["index"] for r in data["positions"] if r["box_above_marked"]] == [1, 2]


def test_unknown_box_heights_are_reviewed_not_fabricated():
    report = plan_review(mission())
    assert any("position_1:roller_total_height" in x for x in report["required_review"])
    assert any("position_2:roller_total_height" in x for x in report["required_review"])


def test_no_save_or_extra_roller_boxes():
    data = mission()
    data["global"]["save_before_salesperson_review"] = True
    assert "saving_must_be_disabled" in validate_mission(data)
    data = mission()
    data["positions"][2]["roller_position"] = {"requested": True, "pricing": "no_price"}
    assert "position_3_unmarked_box_must_not_be_added" in validate_mission(data)


def test_marked_roller_must_have_zero_price_setting_and_sequential_indices():
    data = mission()
    data["positions"][0]["roller_position"]["pricing"] = "priced"
    assert "position_1_box_price_must_be_disabled" in validate_mission(data)
    data = mission()
    data["positions"][1]["index"] = 4
    assert "position_indices_not_sequential" in validate_mission(data)
