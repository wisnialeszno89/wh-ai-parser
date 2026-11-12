"""Read a salesperson's command and run the existing-offer correction lab."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.windowhub_sales_correction import resolve_sales_correction
from tools.check_windowhub_existing_offer_flow import load_fixture, run_forms, run_headless, verify_saved


def main(argv=None):
    from tkinter import TclError

    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--command")
    source.add_argument("--command-file", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command_file and args.command_file.resolve() == args.output.resolve():
            raise ValueError("Wskaż inny plik wyjściowy niż plik polecenia.")
        text = args.command_file.read_text(encoding="utf-8-sig").strip() if args.command_file else args.command
        _, offers = load_fixture()
        original = deepcopy(offers)
        scenario = resolve_sales_correction(text, offers)
        report = run_headless(scenario, offers) if args.headless else run_forms(scenario, offers)
        verify_saved(report, original, scenario)
        for before, after in zip(original, offers):
            if before["number"] != scenario["offer_number"] and before != after:
                raise ValueError("Zmieniła się inna oferta.")
        report["command"] = text
        report["parsed_request"] = scenario["parsed_request"]
        report["test_assumptions"] = ["Fikcyjne oferty bazowe z repo. Kierunki okucia, kolory i pakiet szyb zachowane z wczytanej pozycji."]
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        verify_saved(json.loads(args.output.read_text(encoding="utf-8")), original, scenario)
        print(f"COMMAND_OFFER={scenario['offer_number']} POSITION={scenario['position_reference']}")
        print(f"SIZE={scenario['changes']['width_mm']}x{scenario['changes']['height_mm']} "
              f"POSITIONS={len(report['offer']['positions'])} OTHER_POSITIONS=preserved")
        print("WH_SALES_CORRECTION_RESULT=verified MODE=" + ("headless" if args.headless else "forms"))
        return 0
    except (OSError, ValueError, TclError) as exc:
        print(f"WH_SALES_CORRECTION_RESULT=review\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
