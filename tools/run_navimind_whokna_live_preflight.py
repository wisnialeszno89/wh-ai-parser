"""Inspect actual WindowHub offer scene against a documentation-grounded plan.

No automatic focus. Prepare WindowHub manually during --start-delay.
No clicks, typing, saves, app switching, or HTTP requests.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.knowledge.whokna_offer_guide import load_reference, offer_plan
from app.agent.knowledge.whokna_live_offer_gate import observe_offer_gate
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe manually prepared WH Okna offer")
    parser.add_argument("--map", type=Path)
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--start-delay", type=int, default=12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        print("WH_LIVE_STOP=windows_required")
        return 2
    if not 0 <= args.start_delay <= 30:
        print("WH_LIVE_STOP=bad_start_delay")
        return 2
    icon_map = None
    if args.map is not None:
        if not args.map.is_file():
            print("WH_LIVE_STOP=icon_map_missing")
            return 2
        icon_map = json.loads(args.map.read_text(encoding="utf-8"))
    plan = offer_plan(
        load_reference(), width=args.width, height=args.height,
        quantity=args.quantity, icon_map=icon_map,
    )
    print("WH_LIVE_MODE=READ_ONLY_GUIDED_PREFLIGHT", flush=True)
    print("WH_LIVE_FOCUS_MODE=MANUAL_SAFE", flush=True)
    print("WH_LIVE_PREPARE=Activate WindowHub test offer now", flush=True)
    time.sleep(args.start_delay)
    loop = create_windows_desktop_agent_control_loop()
    gate, scene = observe_offer_gate(loop)
    output = {
        "schema": "navimind.whokna.live_guided_preflight.v1",
        "gate": gate.__dict__,
        "request": plan["request"],
        "stages": [
            {
                "id": stage["id"],
                "title": stage["title"],
                "source_rule_ids": [r["id"] for r in stage["source_rules"]],
                "tool_matches": len(stage["tool_hypotheses"]),
                "state": "not_started",
            }
            for stage in plan["stages"]
        ],
        "desktop_actions": 0,
        "ready_for_execution": False,
    }
    print("WH_LIVE_GATE=" + ("PASS" if gate.ok else "STOP"))
    print("WH_LIVE_STAGE=" + gate.scene_stage)
    print("WH_LIVE_REASON=" + gate.reason)
    print("WH_LIVE_ELEMENTS=" + str(len(scene.elements)))
    print("WH_LIVE_PLAN_STAGES=" + str(len(plan["stages"])))
    print("WH_LIVE_ACTIONS_EXECUTED=0")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print("WH_LIVE_OUTPUT=" + str(args.output))
    return 0 if gate.ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
