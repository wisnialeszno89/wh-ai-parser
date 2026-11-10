"""Prepare a mixed test offer offline from a Zirkon draft and two FIX/RU cases."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_fix_ru_plan import plan_fix_ru
from tools.test_single_sash_construction_lab import check_single_sash


def prepare_mixed_offer(rows):
    positions = []
    for kind, row in rows:
        entry = {"position": row["position"], "kind": kind, "source": row}
        try:
            if kind == "single_sash":
                entry["simulation"] = check_single_sash(row)
                entry["status"] = "simulated"
            elif kind == "fix_ru":
                steps = plan_fix_ru(
                    width_mm=row.get("width_mm"), height_mm=row.get("height_mm"),
                    layout=row.get("layout"), split_from_left_mm=row.get("split_from_left_mm"),
                    opening_code=row.get("opening"),
                )
                entry["steps"] = [
                    {"tool": step.gui_tool.value, "target": step.element_id, "side": step.side.value,
                     "parent": step.parent_id, "parameters": step.properties}
                    for step in steps
                ]
                entry["status"] = "planned"
            else:
                raise ValueError(f"Nieobsługiwany rodzaj pozycji: {kind}.")
        except ValueError as exc:
            entry.update(status="review", reason=str(exc))
        positions.append(entry)
    return {"status": "sales_review_required", "mode": "offline", "positions": positions}


def sample_positions(draft):
    if not isinstance(draft, dict) or draft.get("status") != "technical_draft" or not isinstance(draft.get("positions"), list):
        raise ValueError("Oczekiwano szkicu technicznego Zirkon.")
    selected = [row for row in draft["positions"] if isinstance(row, dict) and row.get("position") == "10.0"]
    if len(selected) != 1:
        raise ValueError("Szkic musi zawierać jedną pozycję Zirkon 10.0.")
    fix_ru = {"quantity": 1, "width_mm": 1600, "height_mm": 1400, "layout": "FIX+RU", "opening": "DKL"}
    return [
        ("single_sash", selected[0]),
        ("fix_ru", dict(fix_ru, position="FIX-RU-01", split_from_left_mm=650)),
        ("fix_ru", dict(fix_ru, position="FIX-RU-02")),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zirkon-draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Save the offline handoff report as JSON.")
    args = parser.parse_args()
    try:
        if args.output and args.output.resolve() == args.zirkon_draft.resolve():
            raise ValueError("Wskaż inny plik wyjściowy niż szkic źródłowy.")
        draft = json.loads(args.zirkon_draft.read_text(encoding="utf-8-sig"))
        report = prepare_mixed_offer(sample_positions(draft))
        if args.output:
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"WH_MIXED_OFFER_RESULT=error\n{exc}", file=sys.stderr)
        return 2
    statuses = []
    for row in report["positions"]:
        statuses.append(row["status"])
        reason = f" REASON={row['reason']}" if "reason" in row else ""
        print(f"POSITION={row['position']} STATUS={row['status']}{reason}")
    print(f"DRAFT_OFFER_STATUS={report['status']}")
    verified = statuses == ["simulated", "planned", "review"] and (
        "Brakuje wymiaru podziału" in report["positions"][2]["reason"]
    )
    print("WH_MIXED_OFFER_RESULT=" + ("verified" if verified else "review"))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
