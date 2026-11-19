"""Validated sales enquiry → bounded NaviMind V2 goal and knowledge.

This is a planning bridge, not a claim of WindowHub execution. The mission's
values are untrusted source requirements. A live readback alone establishes
application state. Keep source quotation metadata out of the model request.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.prepare_windowhub_enquiry_mission import validate_mission

MAX_MISSION_BYTES = 48_000
MAX_POSITIONS = 24


def load_sales_mission(path: Path) -> dict:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError("mission_file_missing")
    if path.stat().st_size > MAX_MISSION_BYTES:
        raise ValueError("mission_file_oversized")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("mission_json_invalid") from exc
    if not isinstance(data, dict):
        raise ValueError("mission_not_object")
    problems = validate_mission(data)
    if problems:
        raise ValueError("mission_invalid:" + ",".join(problems[:8]))
    if len(data["positions"]) > MAX_POSITIONS:
        raise ValueError("mission_too_many_positions")
    return data


def mission_model_context(mission: dict) -> dict:
    """Small JSON-compatible planning context without source photo/customer leakages."""
    issues = []
    positions = []
    for row in mission["positions"]:
        idx = row["index"]
        window = {
            "position": idx,
            "quantity": row["quantity"],
            "window_width_mm": row["width_mm"],
            "window_height_mm": row["height_mm"],
            "dimension_basis": row.get("dimension_basis", "unverified"),
            "layout": row.get("layout", "unverified"),
            "opening": row.get("opening", "requires_live_readback"),
            "box_requested": bool(row.get("box_above_marked")),
            "status": "not_verified_in_windowhub",
        }
        if row.get("sections_width_mm"):
            window["section_widths_mm"] = row["sections_width_mm"]
        if row.get("box_above_marked"):
            box = row["roller_position"]
            window["box"] = {
                "pricing": "no_price",
                "height_mm": box.get("box_height_mm"),
                "total_height_mm": box.get("overall_height_mm"),
                "source": "marked_on_customer_drawing",
                "dimension_rule": "verify_installed_catalogue_and_mounting_convention",
            }
            if box.get("overall_height_mm") is None:
                issues.append("position_" + str(idx) + ":box_total_height_requires_catalogue")
        positions.append(window)
    settings = mission["global"]
    return {
        "schema": "navimind.whokna.sales_task_context.v1",
        "mission_id": mission["mission_id"],
        "customer_lookup": "existing_exact_record",
        "windows": positions,
        "manufacturer_first": True,
        "system_requested": settings["system"],
        "colors_requested": {
            "outside": settings["color_external"],
            "inside": settings["color_internal"],
        },
        "glazing_panes_requested": settings["glazing_panes"],
        "window_discount_percent_requested": settings["discount_window_percent"],
        "box_price_policy": "excluded",
        "document_state": "not_started_or_unverified",
        "unresolved": issues,
        "completion": "unsaved_offer_on_screen_requires_salesperson_review",
        "save_allowed": False,
        "send_allowed": False,
        "all_positions_require_live_readback": True,
    }


def mission_goal(mission: dict) -> str:
    """Human-meaningful objective; field details stay in structured knowledge."""
    return (
        "WH Okna: prepare one UNSAVED draft offer for exact existing customer "
        + mission["customer"]["exact_name"]
        + ". Use the observed screen and manufacturer catalogue to configure "
        + str(len(mission["positions"])) + " window positions and "
        + str(sum(bool(p["box_above_marked"]) for p in mission["positions"]))
        + " marked top boxes. Follow mission knowledge for each dimension, "
        + "configuration, 20% window-only discount and no-price boxes. "
        + "Choose nearest proven compatible catalogue alternatives and report "
        + "every deviation. If construction is impossible, leave an evidenced "
        + "dimensioned incomplete position where supported; proceed to the next. "
        + "NEVER SAVE or send; end with a factual salesperson review report."
    )


def mission_knowledge(base: dict, mission: dict) -> dict:
    if not isinstance(base, dict):
        raise TypeError("base_knowledge_must_be_object")
    return {**base, "active_sales_mission": mission_model_context(mission)}
