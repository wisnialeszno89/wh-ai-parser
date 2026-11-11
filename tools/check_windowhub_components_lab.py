"""Check archived builder icons and single-sash hardware/glazing combinations offline."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_single_sash_lab import simulate_single_tilt_turn
from tools.check_windowhub_builder_sequence import main as check_archive


def check_component_cases():
    cases = []
    for panes in (2, 3):
        for opening in ("DKL", "DKR"):
            for auto_direction in ("LEFT", "RIGHT"):
                request = {"width_mm": 1000, "height_mm": 1000, "opening": opening, "glazing_panes": panes}
                result = simulate_single_tilt_turn(request, auto_direction=auto_direction)
                stages = [step["stage"] for step in result["trace"]]
                desired_direction = "LEFT" if opening == "DKL" else "RIGHT"
                expected = ["frame", "sash", "glazing", "hardware"]
                if desired_direction != auto_direction:
                    expected.append("inversion")
                if stages != expected or result["direction"] != desired_direction or result["panes"] != panes:
                    raise ValueError("Odczyt nie potwierdził oczekiwanej kolejności, kierunku lub liczby szyb.")
                cases.append({"request": request, "simulation": result, "status": "simulated"})
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if check_archive() != 0:
            raise ValueError("Zrzuty archiwalne nie potwierdziły sekwencji ikon.")
        cases = check_component_cases()
        report = {"mode": "offline", "status": "sales_review_required",
                  "archived_builder": "verified", "cases": cases}
        if args.output:
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for case in cases:
            request, result = case["request"], case["simulation"]
            inversion = "inversion" in [step["stage"] for step in result["trace"]]
            print(f"OPENING={request['opening']} PANES={result['panes']} "
                  f"AUTO={result['automatic_direction']} INVERSION={inversion} "
                  f"FINAL={result['direction']} HARDWARE={result['hardware_product']} RESULT=simulated")
        print("WH_COMPONENTS_LAB_RESULT=verified CASES=" + str(len(cases)))
        return 0
    except (OSError, ValueError) as exc:
        print(f"WH_COMPONENTS_LAB_RESULT=review\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
