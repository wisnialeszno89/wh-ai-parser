"""Offline preflight for a photographed WH Okna sales enquiry.

This intentionally does NOT drive the GUI or claim an offer exists. It emits a
precise mission contract for the existing supervised WindowHub agent runners.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research/scenarios/top_trans_20261119_4windows.json"


def validate_mission(mission: dict) -> list[str]:
    errors = []
    if mission.get("schema") != "navimind.windowhub.enquiry_mission.v1":
        errors.append("schema_unknown")
    customer = mission.get("customer", {})
    if not customer.get("exact_name"):
        errors.append("exact_customer_missing")
    settings = mission.get("global", {})
    if settings.get("save_before_salesperson_review") is not False:
        errors.append("saving_must_be_disabled")
    if settings.get("send_before_salesperson_review") is not False:
        errors.append("sending_must_be_disabled")
    rows = mission.get("positions", ())
    if not isinstance(rows, list) or not rows:
        return errors + ["positions_missing"]
    if [row.get("index") for row in rows] != list(range(1, len(rows) + 1)):
        errors.append("position_indices_not_sequential")
    for row in rows:
        idx = row.get("index", "?")
        for field in ("width_mm", "height_mm", "quantity"):
            value = row.get(field)
            if type(value) is not int or value < 1:
                errors.append(f"position_{idx}_invalid_{field}")
        if row.get("box_above_marked"):
            box = row.get("roller_position")
            if not isinstance(box, dict) or not box.get("requested"):
                errors.append(f"position_{idx}_marked_box_missing")
            elif box.get("pricing") != "no_price":
                errors.append(f"position_{idx}_box_price_must_be_disabled")
        elif row.get("roller_position"):
            errors.append(f"position_{idx}_unmarked_box_must_not_be_added")
    return errors


def plan_review(mission: dict) -> dict:
    errors = validate_mission(mission)
    if errors:
        raise ValueError(";".join(errors))
    positions = mission["positions"]
    blockers = list(mission.get("interpretation_flags", []))
    for row in positions:
        if row.get("box_above_marked"):
            box = row["roller_position"]
            if box.get("overall_height_mm") is None:
                blockers.append(f"position_{row['index']}:roller_total_height_requires_live_catalogue")
    return {
        "mission": mission["mission_id"],
        "customer": mission["customer"]["exact_name"],
        "planned_window_count": len(positions),
        "planned_roller_box_count": sum(bool(row["box_above_marked"]) for row in positions),
        "planned_discount_percent": mission["global"]["discount_window_percent"],
        "required_review": blockers,
        "executor_actions_performed": 0,
        "windowhub_offer_created": False,
        "windowhub_offer_saved": False,
        "next": "Supervised Windows GUI execution and verified salesperson review",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mission", type=Path, default=DEFAULT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    mission = json.loads(args.mission.read_text(encoding="utf-8"))
    try:
        result = plan_review(mission)
    except ValueError as exc:
        print("WH_MISSION_INVALID=" + str(exc))
        return 2
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
