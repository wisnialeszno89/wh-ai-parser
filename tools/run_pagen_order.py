"""NaviMind browser pilot for structured window orders."""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.pagen_order import read_pagen_order
from app.agent.offers.pagen_configurator import PagenOrder, fill_pagen_order, inspect_pagen_catalog


def choose_catalog_options(catalog, read=input):
    selected = {}
    for key, title in (("color", "Kolor dla całego formularza"), ("glazing", "Szyba dla całego formularza")):
        field = catalog["catalog"][key]
        options = [item for item in field["options"] if field["enabled"] and item["value"] and not item["disabled"]]
        print(f"\n{title}. 0 = pozostaw bez wytycznych")
        for index, option in enumerate(options, 1):
            print(f"  {index}. {option['label']}")
        answer = read("Wpisz numer opcji: ").strip()
        if not answer.isascii() or not answer.isdecimal() or not 0 <= int(answer) <= len(options):
            raise ValueError("Podano nieprawidłowy numer opcji katalogowej.")
        selected[key] = None if int(answer) == 0 else options[int(answer) - 1]["label"]
    return selected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--order-file", type=Path, help="UTF-8 CSV (separator ;) or JSON.")
    source.add_argument("--specification-file", type=Path, help="Shared window-offer/1 exported from NaviMind text/PDF reading.")
    parser.add_argument("--execute-live", action="store_true", help="Open PAGEN and fill the public form.")
    parser.add_argument("--headed", action="store_true", help="Show the Chromium window.")
    parser.add_argument("--keep-open", action="store_true", help="Wait for Enter before closing the visible test window.")
    parser.add_argument("--output", type=Path, help="Write the verified form readback as JSON.")
    parser.add_argument("--inspect-catalog", action="store_true", help="Read profile, type, color and glazing catalogs without filling positions.")
    parser.add_argument("--choose-options", action="store_true", help="Choose color and glazing from numbered live catalog lists.")
    parser.add_argument("--color", help="Exact color option label; applies to the whole form.")
    parser.add_argument("--glazing", help="Exact glazing option label; applies to the whole form.")
    parser.add_argument("--save-order", type=Path, help="Save the resolved specification as JSON for automatic reuse.")
    args = parser.parse_args(argv)
    if not args.order_file and not args.specification_file and not args.inspect_catalog:
        parser.error("Podaj --order-file, --specification-file albo --inspect-catalog")
    if args.specification_file and (args.inspect_catalog or args.choose_options or args.color is not None or args.glazing is not None):
        parser.error("Nie nadpisuj pól wspólnej specyfikacji flagami; popraw źródłowe zapytanie/specyfikację.")
    if args.inspect_catalog and (args.color is not None or args.glazing is not None or args.choose_options):
        parser.error("Odczyt katalogu nie łączy się z wyborem koloru/szyby")
    if args.choose_options and (args.color is not None or args.glazing is not None):
        parser.error("Użyj --choose-options albo --color/--glazing")
    if args.inspect_catalog and args.save_order:
        parser.error("--save-order wymaga zlecenia, nie samego odczytu katalogu")
    if args.output and args.save_order and args.output.resolve() == args.save_order.resolve():
        parser.error("Raport i zlecenie muszą mieć osobne pliki")
    if args.keep_open and not args.headed:
        parser.error("--keep-open requires --headed")

    specification_plan = None
    try:
        order = read_pagen_order(args.order_file) if args.order_file else None
        if args.specification_file:
            from app.agent.intake.window_offer_specification import read_offer_specification, prepare_pagen_specification
            specification_plan = prepare_pagen_specification(read_offer_specification(args.specification_file))
            if specification_plan['status'] != 'ready_for_form':
                print('PAGEN_RESULT=specification_review')
                print(json.dumps(specification_plan, ensure_ascii=False, indent=2))
                return 6
            order = PagenOrder.from_dict(specification_plan['order'])
        overrides = {key: getattr(args, key) for key in ("color", "glazing") if getattr(args, key) is not None}
        if any(not value.strip() for value in overrides.values()):
            raise ValueError("Nazwa opcji nie może być pusta.")
        if overrides:
            order = replace(order, **{key: value.strip() for key, value in overrides.items()})
    except (csv.Error, OSError, ValueError) as exc:
        print(f"PAGEN_RESULT=invalid_order\n{exc}", file=sys.stderr)
        return 2

    if not args.execute_live:
        if args.inspect_catalog or args.choose_options:
            print("PAGEN_RESULT=live_catalog_required Dodaj --execute-live.")
            return 2
        if args.save_order:
            try:
                args.save_order.write_text(json.dumps(order.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                print(f"PAGEN_RESULT=review\n{exc}", file=sys.stderr)
                return 6
        if specification_plan:
            print('PAGEN_SPECIFICATION=prepared')
            print(json.dumps(specification_plan, ensure_ascii=False, indent=2))
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
                    page = context.new_page()
                    if args.inspect_catalog or args.choose_options:
                        catalog = inspect_pagen_catalog(page, order.profile if order else None)
                    if args.inspect_catalog:
                        report = catalog
                        for key, field in catalog["catalog"].items():
                            print(f"CATALOG={key} ENABLED={field['enabled']}")
                            for item in field["options"]:
                                if item["value"] and not item["disabled"]:
                                    print("  " + item["label"])
                    else:
                        if args.choose_options:
                            order = replace(order, **choose_catalog_options(catalog))
                        if args.save_order:
                            args.save_order.write_text(json.dumps(order.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                            print("PAGEN_ORDER=saved PATH=" + str(args.save_order), flush=True)
                        report = fill_pagen_order(page, order)
                        if specification_plan:
                            report['specification'] = {key: specification_plan[key] for key in (
                                'source_sha256', 'specification_sha256', 'source_positions', 'scope')}
                    if args.output:
                        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    marker = "PAGEN_CATALOG=observed" if args.inspect_catalog else "PAGEN_READBACK=verified"
                    print(marker + " SUBMITTED=False WH_OFFER_CREATED=False", flush=True)
                    if not args.inspect_catalog:
                        for key, field in report["shared_options"].items():
                            print(f"OPTION={key} STATUS={field['status']} LABEL={field.get('observed_label', '-')}")
                except (Error, ValueError, OSError, EOFError) as exc:
                    print(f"PAGEN_STEP=review {exc}", flush=True)
                    raise
                finally:
                    if args.keep_open:
                        input("Sprawdź formularz w Chromium. Enter w PowerShell zamknie okno: ")
            finally:
                browser.close()
    except (Error, ValueError, OSError, EOFError) as exc:
        print(f"PAGEN_RESULT=review\n{exc}", file=sys.stderr)
        return 6

    if args.inspect_catalog:
        print("PAGEN_RESULT=catalog_observed")
    else:
        print(f"PAGEN_RESULT=verified\nPAGEN_POSITIONS={len(order.positions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
