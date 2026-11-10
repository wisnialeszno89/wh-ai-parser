"""NaviMind browser pilot for structured window orders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.pagen_configurator import PagenOrder, fill_pagen_order


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order-file", type=Path, required=True)
    parser.add_argument("--execute-live", action="store_true", help="Open PAGEN and fill the public form.")
    args = parser.parse_args()

    try:
        order = PagenOrder.from_dict(json.loads(args.order_file.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError) as exc:
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
            browser = playwright.chromium.launch()
            try:
                context = browser.new_context(locale="pl-PL", service_workers="block")
                fill_pagen_order(context.new_page(), order)
            finally:
                browser.close()
    except (Error, ValueError) as exc:
        print(f"PAGEN_RESULT=review\n{exc}", file=sys.stderr)
        return 6

    print(f"PAGEN_RESULT=verified\nPAGEN_POSITIONS={len(order.positions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
