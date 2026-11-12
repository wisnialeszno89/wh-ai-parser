"""Plan a FIX/RU position offline using explicit dimensions and opening direction."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_fix_ru_plan import plan_fix_ru


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width-mm", type=int, required=True)
    parser.add_argument("--height-mm", type=int, required=True)
    parser.add_argument("--layout", required=True, help="Left-to-right order: FIX+RU or RU+FIX.")
    parser.add_argument("--split-from-left-mm", type=int)
    parser.add_argument("--opening", dest="opening_code", help="Direction of the RU sash: DKL or DKR.")
    try:
        steps = plan_fix_ru(**vars(parser.parse_args()))
    except (OSError, ValueError) as exc:
        print(f"WH_FIX_RU_RESULT=review\n{exc}", file=sys.stderr)
        return 2
    print("WH_FIX_RU_RESULT=planned")
    for step in steps:
        print(json.dumps({
            "tool": step.gui_tool.value,
            "target": step.element_id,
            "side": step.side.value,
            "parent": step.parent_id,
            "parameters": step.properties,
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
