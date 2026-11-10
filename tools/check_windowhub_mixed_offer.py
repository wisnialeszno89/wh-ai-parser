"""Prepare a mixed offer offline from a German mail, JSON request or Zirkon test case."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.german_offer_mail import inspect_german_offer_mail
from app.agent.intake.task_document import read_task_document
from app.agent.offers.windowhub_fix_ru_plan import plan_fix_ru
from tools.test_single_sash_construction_lab import check_single_sash


def prepare_mixed_offer(rows):
    positions = []
    for kind, row in rows:
        entry = {"position": row["position"], "kind": kind, "source": row}
        try:
            if kind == "entrance_door":
                raise ValueError("Drzwi wejściowe wymagają osobnego planu konstrukcji.")
            if kind == "stulp_variant":
                reason = ("Potwierdź, czy to warianty do porównania czy oddzielne pozycje, "
                          "oraz ilość i kierunek otwierania.")
                if row.get("mullion_requirement") == "without_movable":
                    reason += " Ustal układ skrzydeł w wersji bez słupka ruchomego."
                if row.get("profile_preference"):
                    reason += " Dobierz system wąskiego profilu."
                if row.get("color_pair"):
                    reason += " Potwierdź przypisanie kolorów do stron."
                raise ValueError(reason)
            quantity = row.get("quantity")
            if type(quantity) is not int or quantity <= 0:
                raise ValueError("Podaj dodatnią całkowitą ilość pozycji.")
            for field in ("opening", "layout"):
                value = row.get(field)
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"Pole {field} musi być tekstem.")
            if kind == "single_sash":
                entry["simulation"] = check_single_sash(row)
                entry["status"] = "simulated"
            elif kind == "fix_ru":
                steps = plan_fix_ru(
                    width_mm=row.get("width_mm"), height_mm=row.get("height_mm"),
                    layout=row.get("layout"), split_from_left_mm=row.get("split_from_left_mm"),
                    opening_code=row.get("opening"),
                )
                entry["steps"] = [
                    {"tool": step.gui_tool.value, "target": step.element_id, "side": step.side.value,
                     "parent": step.parent_id, "parameters": step.properties}
                    for step in steps
                ]
                entry["status"] = "planned"
            elif kind == "window_unspecified":
                raise ValueError("Brakuje jednoznacznego typu konstrukcji. Sprawdź układ pól i opis klienta.")
            else:
                raise ValueError(f"Nieobsługiwany rodzaj pozycji: {kind}.")
        except ValueError as exc:
            entry.update(status="review", reason=str(exc))
        positions.append(entry)
    return {"status": "sales_review_required", "mode": "offline", "positions": positions}


def request_positions(request):
    if not isinstance(request, dict) or not isinstance(request.get("positions"), list) or not request["positions"]:
        raise ValueError("Zapytanie musi zawierać niepustą listę positions.")
    rows = []
    references = set()
    for row in request["positions"]:
        reference = row.get("position") if isinstance(row, dict) else None
        if not isinstance(reference, str) or not reference.strip():
            raise ValueError("Każda pozycja musi mieć identyfikator tekstowy position.")
        if reference.strip() in references:
            raise ValueError(f"Powtórzony identyfikator pozycji: {reference}.")
        references.add(reference.strip())
        rows.append((row.get("kind"), row))
    return rows


def mail_positions(text):
    parsed = inspect_german_offer_mail(text)
    if not parsed:
        raise ValueError("Nie rozpoznano pozycji Fenster ani Haustür w treści maila.")
    rows = []
    for index, row in enumerate(parsed, 1):
        if row["product_type"] == "entrance_door":
            kind = "entrance_door"
        elif row.get("variant_group") is not None:
            kind = "stulp_variant"
        elif row["layout"]:
            kind = "fix_ru"
        elif row["construction"]:
            kind = "single_sash"
        else:
            kind = "window_unspecified"
        rows.append((kind, dict(row, position=f"MAIL-{index:02d}")))
    return rows


def sample_positions(draft):
    if not isinstance(draft, dict) or draft.get("status") != "technical_draft" or not isinstance(draft.get("positions"), list):
        raise ValueError("Oczekiwano szkicu technicznego Zirkon.")
    selected = [row for row in draft["positions"] if isinstance(row, dict) and row.get("position") == "10.0"]
    if len(selected) != 1:
        raise ValueError("Szkic musi zawierać jedną pozycję Zirkon 10.0.")
    fix_ru = {"quantity": 1, "width_mm": 1600, "height_mm": 1400, "layout": "FIX+RU", "opening": "DKL"}
    return [
        ("single_sash", selected[0]),
        ("fix_ru", dict(fix_ru, position="FIX-RU-01", split_from_left_mm=650)),
        ("fix_ru", dict(fix_ru, position="FIX-RU-02")),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--request-file", type=Path, help="UTF-8 JSON with every position in the request.")
    source.add_argument("--mail-file", type=Path, help="German enquiry saved as a UTF-8 text file.")
    source.add_argument("--zirkon-draft", type=Path, help="Run the original fixed Zirkon test case.")
    parser.add_argument("--output", type=Path, help="Save the offline handoff report as JSON.")
    args = parser.parse_args()
    try:
        input_file = args.mail_file or args.request_file or args.zirkon_draft
        if args.output and args.output.resolve() == input_file.resolve():
            raise ValueError("Wskaż inny plik wyjściowy niż plik źródłowy.")
        if args.mail_file:
            text = read_task_document(input_file, max_chars=12_001)
            if len(text) > 12_000:
                raise ValueError("Tekst przekracza 12 000 znaków.")
            rows = mail_positions(text)
        else:
            data = json.loads(input_file.read_text(encoding="utf-8-sig"))
            rows = request_positions(data) if args.request_file else sample_positions(data)
        report = prepare_mixed_offer(rows)
        if args.output:
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"WH_MIXED_OFFER_RESULT=error\n{exc}", file=sys.stderr)
        return 2
    statuses = []
    for row in report["positions"]:
        statuses.append(row["status"])
        reason = f" REASON={row['reason']}" if "reason" in row else ""
        print(f"POSITION={row['position']} STATUS={row['status']}{reason}")
    print(f"DRAFT_OFFER_STATUS={report['status']}")
    if not args.zirkon_draft:
        print("WH_MIXED_OFFER_RESULT=processed")
        return 0
    verified = statuses == ["simulated", "planned", "review"] and (
        "Brakuje wymiaru podziału" in report["positions"][2]["reason"]
    )
    print("WH_MIXED_OFFER_RESULT=" + ("verified" if verified else "review"))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
