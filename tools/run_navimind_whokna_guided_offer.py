"""Plan a WH Okna offer using manual reference and Explorer OCR memory.

READ ONLY. This command has no desktop automation, clicks or network calls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.agent.knowledge.whokna_offer_guide import load_reference, offer_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="WH Okna documentation-grounded offer preflight")
    parser.add_argument("--map", type=Path)
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--glazing", default="2-szybowy")
    parser.add_argument("--outer-color", default="antracyt")
    parser.add_argument("--inner-color", default="biały")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    icon_map = None
    if args.map:
        if not args.map.is_file():
            print("WH_GUIDE_STOP=icon_map_not_found")
            return 2
        icon_map = json.loads(args.map.read_text(encoding="utf-8"))
    plan = offer_plan(
        load_reference(), width=args.width, height=args.height,
        quantity=args.quantity, glazing=args.glazing,
        outer_color=args.outer_color, inner_color=args.inner_color,
        icon_map=icon_map,
    )
    print("WH_GUIDE_MODE=PLAN_ONLY_NO_CLICKS")
    print("WH_GUIDE_SOURCE=" + plan["source"]["url"])
    print("WH_GUIDE_STAGES=" + str(len(plan["stages"])))
    for i, stage in enumerate(plan["stages"]):
        matches = stage["tool_hypotheses"]
        print(
            f"WH_STAGE_{i}={stage['id']} "
            f"TOOL_MATCHES={len(matches)} "
            "STATE=not_started "
            + ("TOOL=" + repr(matches[0]["label_hypothesis"]) if matches else "")
        )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("WH_GUIDE_OUTPUT=" + str(args.output))
    print("WH_GUIDE_ACTIONS_EXECUTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
