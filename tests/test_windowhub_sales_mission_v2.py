"""Offline contract checks for the real enquiry → NaviMind V2 bridge."""
import json
from pathlib import Path

import pytest

from app.agent.bridge.windowhub_sales_mission_v2 import (
    load_sales_mission, mission_goal, mission_knowledge, mission_model_context,
)
from tools.prepare_windowhub_enquiry_mission import DEFAULT


def test_four_windows_are_sent_as_structured_model_knowledge():
    mission = load_sales_mission(DEFAULT)
    data = mission_model_context(mission)
    assert data["schema"] == "navimind.whokna.sales_task_context.v1"
    assert data["save_allowed"] is False
    assert data["send_allowed"] is False
    assert len(data["windows"]) == 4
    assert [p["window_height_mm"] for p in data["windows"]] == [1010, 1010, 950, 980]
    assert [p["position"] for p in data["windows"] if p["box_requested"]] == [1, 2]
    assert data["windows"][0]["box"]["total_height_mm"] is None
    assert data["window_discount_percent_requested"] == 20


def test_no_invented_gui_success_or_different_customer_name():
    mission = load_sales_mission(DEFAULT)
    context = mission_knowledge({"application": "WindowHub"}, mission)
    assert context["application"] == "WindowHub"
    assert "customer" not in context["active_sales_mission"]  # explicit name only in goal
    assert all(p["status"] == "not_verified_in_windowhub"
               for p in context["active_sales_mission"]["windows"])
    goal = mission_goal(mission)
    assert "Top Trans Janik Artur" in goal
    assert "Hartmut Zingelmann" not in goal
    assert "NEVER SAVE" in goal


def test_reject_missing_invalid_or_oversized_mission(tmp_path):
    with pytest.raises(ValueError, match="mission_file_missing"):
        load_sales_mission(tmp_path / "nothing.json")
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"schema":"unknown"}', encoding="utf-8")
    with pytest.raises(ValueError, match="mission_invalid"):
        load_sales_mission(invalid)
    huge = tmp_path / "huge.json"
    huge.write_text("x" * 48001, encoding="utf-8")
    with pytest.raises(ValueError, match="mission_file_oversized"):
        load_sales_mission(huge)


def test_reject_mission_with_save_enabled(tmp_path):
    data = json.loads(Path(DEFAULT).read_text(encoding="utf-8"))
    data["global"]["save_before_salesperson_review"] = True
    path = tmp_path / "unsafe.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="saving_must_be_disabled"):
        load_sales_mission(path)
