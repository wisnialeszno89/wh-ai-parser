"""Verify glazing choices against explicit synthetic records and one archived label."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_glass_selection import select_glass_package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        fixture = json.loads((ROOT / "examples/windowhub-glass-selection-lab.json").read_text(encoding="utf-8"))
        reports = []
        for case in fixture["cases"]:
            result = select_glass_package(case["requirements"], fixture["candidates"])
            if result["status"] != case["expected_status"] or result.get("selected", {}).get("id") != case.get("expected_id"):
                raise ValueError(f"Wynik doboru różni się od oczekiwanego: {case['name']}.")
            reports.append(dict(name=case["name"], result=result))
        archived_label = "4plth/18CR/4/18C/4 Ug=0.5"
        archive = ROOT / "research/extracted/utf16_strings.txt"
        if archived_label not in archive.read_text(encoding="utf-8").splitlines():
            raise ValueError("Nie znaleziono etykiety archiwalnego pakietu w repo.")
        # The archived label does not establish the spacer brand or a usable WH record ID.
        archived = select_glass_package(
            {"spacer": "Swisspacer Ultimate"},
            [{"id": "ARCHIVE-LABEL", "label": archived_label}],
        )
        if archived["status"] != "review":
            raise ValueError("Niepełna etykieta archiwalna wymaga weryfikacji.")
        reports.append(dict(name="archived_spacer_unknown", result=archived))
        if args.output:
            args.output.write_text(json.dumps({
                "mode": "offline", "catalog": fixture["data_kind"],
                "status": "sales_review_required", "cases": reports,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for case in reports:
            result = case["result"]
            print(f"CASE={case['name']} STATUS={result['status']} "
                  f"PACKAGE={result.get('selected', {}).get('id', 'sales_review')}")
        print(f"WH_GLASS_SELECTION_RESULT=verified CASES={len(reports)}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"WH_GLASS_SELECTION_RESULT=review\n{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
