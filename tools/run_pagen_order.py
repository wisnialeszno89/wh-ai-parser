"""NaviMind browser pilot for structured window orders."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.pagen_order import read_pagen_order
from app.agent.offers.pagen_configurator import fill_pagen_order


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order-file", type=Path, required=True, help="UTF-8 CSV (separator ;) or JSON.")
    parser.add_argument("--execute-live", action="store_true", help="Open PAGEN and fill the public form.")
    parser.add_argument("--headed", action="store_true", help="Show the Chromium window.")
    parser.add_argument("--keep-open", action="store_true", help="Wait for Enter before closing the visible test window.")
    parser.add_argument("--output", type=Path, help="Write the verified form readback as JSON.")
    args = parser.parse_args()
    if args.keep_open and not args.headed:
        parser.error("--keep-open requires --headed")

    try:
        order = read_pagen_order(args.order_file)
    except (csv.Error, OSError, ValueError) as exc:
        print(f"PAGEN_RESULT=invalid_order\n{exc}", file=sys.stderr)
        return 2

    if not args.execute_live:
        print(f"PAGEN_RESULT=order_validated\nPAGEN_POSITIONS={len(order.positions)}")
        return 0

    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        print("Zainstaluj Playwright: python -m pip install playwright", file=sys.stderr)
        return 2

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not args.headed)
            try:
                context = browser.new_context(locale="pl-PL", service_workers="block")
                try:
                    report = fill_pagen_order(context.new_page(), order)
                    if args.output:
                        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print("PAGEN_READBACK=verified SUBMITTED=False WH_OFFER_CREATED=False", flush=True)
                finally:
                    if args.keep_open:
                        input("Sprawdź formularz w Chromium. Enter w PowerShell zamknie okno: ")
            finally:
                browser.close()
    except (Error, ValueError, OSError) as exc:
        print(f"PAGEN_RESULT=review\n{exc}", file=sys.stderr)
        return 6

    print(f"PAGEN_RESULT=verified\nPAGEN_POSITIONS={len(order.positions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
