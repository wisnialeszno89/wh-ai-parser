"""Preview a validated enquiry's outstanding review fields without WindowHub.

This OFFLINE command is a planning report. It cannot claim customer selection,
created positions, validated discounts or successful GUI operations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.bridge.windowhub_sales_mission_review import (
    build_review_report, compact_review_summary,
)
from app.agent.bridge.windowhub_sales_mission_v2 import load_sales_mission


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sales-mission", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="Write report JSON to stdout")
    args = parser.parse_args(argv)
    try:
        mission = load_sales_mission(args.sales_mission)
        report = build_review_report(mission)
    except (OSError, ValueError, KeyError) as exc:
        print("MISSION_REVIEW_ERROR=" + type(exc).__name__, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("OFFLINE_PREVIEW=True")
        print("WINDOWHUB_ACTIONS_EXECUTED=False")
        print(compact_review_summary(report))
        for item in report["unresolved"]:
            print("REVIEW_REQUIRED=" + str(item["position"]) + ":" + str(item["field"])
                  + ":" + str(item["status"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
